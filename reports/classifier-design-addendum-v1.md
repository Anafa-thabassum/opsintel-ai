# Classifier design addendum v1

**Status: revised design for approval; implementation is not approved.** The
role and cause-specific criteria below are proposals awaiting final approval;
they have not been empirically validated. This addendum clarifies the
architecture proposal after review of
[`classifier-error-analysis-v1.md`](classifier-error-analysis-v1.md),
[`classifier-architecture-proposal-v1.md`](classifier-architecture-proposal-v1.md),
`app/investigator.py`, `app/main.py`, and `scripts/evaluate_holdout.py`.
Design-only: no implementation, frozen evaluation asset, dataset, benchmark,
submission asset, or historical report was changed. No tests or evaluations
were run.

## Canonical model: four separate concepts

These are independent dimensions. A value in one must not imply a value in
another.

| Concept | Canonical contract |
|---|---|
| Evidence assessment | `evidence_assessment.status` is `sufficient`, `insufficient`, or `conflicting`. It records evidence refs, source identity, timestamps when available, and assessment reason. `sufficient` means enough relevant, traceable evidence exists for the stated classification; it does not prove a cause. Conflicting claims are preserved on both sides. |
| Classification | `classification.symptom_category` is one of `delayed_run`, `duplicate_data`, `timeout`, `schema_mismatch`, `dependency_failure`, `early_termination`, `incomplete_data`, or null. `classification.status` is `supported` or `unresolved`, based only on evidence for the symptom/category. A category requires positive, non-negated, relevant evidence. |
| Causal assessment | `causal_assessment.candidates[]` contains hypotheses only, each with supporting and contradicting evidence refs and the next verification step. `causal_assessment.status` is `not_assessed`, `candidates_available`, `blocked`, or `confirmed`. `causal_assessment.confirmed_root_cause` is null unless the confirmation workflow below succeeds. Empty candidates are valid. |
| Decision summary | `resolution_status` is a summary derived from classification and causal assessment: `unresolved` if classification is unresolved; `candidate_only` if a symptom is supported but no cause is confirmed; `confirmed` only after the root-cause confirmation gate passes. It is not lifecycle state. |
| Incident lifecycle | Lifecycle is the operational state owned by the incident workflow (for example, open, investigating, resolved, or closed), not a classifier result. The classifier does not infer, change, or close the incident. In particular, `candidate_only` does not mean fixed, resolved, or solved. |

### Classification status semantics

- **`candidate_only`** means a symptom/category is supported by relevant,
  traceable evidence, but no root cause is confirmed. The causal candidate
  list may be empty. If no causal hypothesis has sufficient support, return
  an explicit explanation such as “Symptom supported; no causal hypothesis is
  sufficiently evidenced.” Do not invent a candidate to fill the list. This
  is a decision summary, not `classification.status` and not proof that the
  incident is solved.
- **`unresolved`** means evidence is insufficient to assign a defensible
  symptom category, or material ambiguity prevents reliable classification.
  Include a case-specific reason and identify missing or contradictory
  evidence. If claims conflict but a separate symptom is independently
  supported, retain that symptom and expose the conflict; use `unresolved`
  only when the conflict prevents a reliable category decision.
- **`confirmed`** is a decision summary available only when a root cause has
  passed the human confirmation workflow. It does not imply the incident is
  remediated, resolved, or closed.
- **`confirmed_root_cause`** remains null unless predefined criteria and
  traceable supporting evidence pass the human-controlled confirmation
  workflow. Neither a supported symptom, candidate, confidence score,
  deterministic classifier, nor optional LLM can promote it.

## Conflict and legacy API mapping

In the canonical model, conflicting evidence is represented in
`evidence_assessment.status=conflicting` and its claim-level details; it is
not an operational symptom category. The legacy `category` field continues
to support existing consumers:

| Canonical result | Legacy `category` value |
|---|---|
| A supported symptom, with or without a non-blocking conflict | That symptom category |
| Conflict blocks a defensible symptom choice | `conflicting_evidence` |
| No defensible symptom and no blocking conflict | `unclassified` |

Thus `conflicting_evidence` stays available for compatibility but is not
counted as a canonical symptom. Keep current API fields and types, including
the classifier tuple `(category, hypothesis, next_action)`, investigation
fields (`category`, `hypothesis`, `confidence`, `matched_categories`,
`tie_break_reason`, and `root_causes`), and root-cause assessment fields.
Add the canonical model under a versioned `classification`/assessment object;
do not remove or silently redefine legacy fields. A breaking change requires
an explicitly versioned API and separate approval.

### `candidates_only` compatibility

The current `assess_root_causes` returns `root_causes.resolution_status` as
`candidates_only` if its candidate list is non-empty and `unresolved` if the
list is empty. The current evaluator instead derives `candidate_only` from
any category other than `unclassified`; it does not consume the assessor
status. These meanings differ.

Canonical `resolution_status` is `candidate_only`, `unresolved`, or
`confirmed`, derived from independent classification and causal-assessment
fields; it is not based on whether the candidate list happens to be empty.
During migration:

- Keep legacy `root_causes.resolution_status` and its current behavior as a
  compatibility alias: non-empty legacy candidates map to `candidates_only`,
  empty list maps to `unresolved`.
- Populate canonical `classification.status` independently. A supported
  symptom with an empty causal-candidate list has
  `classification.status=supported`, `causal_assessment.status=not_assessed`
  (or `blocked` if a
  specific hypothesis was rejected for insufficient/contradictory evidence),
  and `resolution_status=candidate_only`, plus an explicit no-supported-cause
  explanation. The legacy alias may remain `unresolved`; document this
  divergence until consumers migrate, and do not silently overwrite legacy
  behavior.
- If the confirmation workflow passes, `classification.status` remains
  `supported`, `causal_assessment.status=confirmed`, and
  `resolution_status=confirmed`; incident lifecycle remains unchanged.
- If classification is unresolved, canonical status is `unresolved` even if
  a speculative cause phrase exists. Preserve legacy fields and mappings per
  the conflict table above.

The existing `confirmed_root_cause: null` behavior is preserved. The current
classifier receives log strings rather than evidence references; the
assessor derives references from `source` plus `run_id`/`log_id`, and can
fall back to `EVIDENCE-{index}`. That generated label alone is not source
provenance and cannot satisfy canonical traceability.

## Proposed role-based root-cause confirmation

**Proposed; awaiting final approval; not empirically validated.** The
deterministic classifier and optional LLM may extract evidence and propose
candidates only. Neither may set or promote `confirmed_root_cause`.

1. An **investigator** may submit a cause hypothesis, evidence packet,
   explanation, and the applicable versioned verification checklist. The
   submission remains a candidate; the submitter cannot confirm it by
   changing a status or writing a narrative.
2. An **authorized root-cause reviewer** must have an explicit, auditable
   reviewer grant defined by the project owner/admin. The reviewer checks the
   evidence and each applicable criterion, then records approve, reject, or
   needs-more-evidence, with rationale, reviewer identity/role, and timestamp.
   Proposed safeguard: the reviewer is a different person from the
   investigator who submitted the hypothesis.
3. Approval is allowed only if all mandatory positive evidence and verification
   criteria below pass, provenance resolves to source records, and no material
   contradiction remains. Human approval cannot override insufficient or
   contradictory evidence. Reject or needs-more-evidence leaves
   `confirmed_root_cause=null` and `causal_assessment.status=blocked` (or
   candidates remain available but unconfirmed).
4. Record the approved causal statement, checklist/version, criterion-level
   results, evidence refs, verification method/result, alternatives and
   contradictions reviewed, reviewer decision/rationale/identity/role, and
   timestamp. Populate `confirmed_root_cause` only after this record passes
   validation.
5. Confirmation does not change incident lifecycle. The lifecycle owner
   separately records remediation and any transition to resolved/closed.

The authorized role name/grant process and reviewer independence rule are
proposals awaiting final approval. No existing permission or confirmation
workflow is assumed.

## Proposed cause-specific verification criteria

The following are proposed minimum gates for confirming a causal explanation.
They distinguish **symptom evidence** (enough to classify what happened) from
**causal evidence** (evidence for why it happened and the mechanism). A symptom
may be `candidate_only` with no causal candidate. The criteria are design
proposals, not empirically validated rules; they must be reviewed and versioned
before implementation or use in a human study.

| Supported class | Symptom evidence (classification only) | Additional positive causal evidence required to confirm | Disqualifying conditions; missing or conflicting evidence |
|---|---|---|---|
| `delayed_run` | Scheduler/source scheduled and actual start times for the same run, comparable timezone/clock basis, and an applicable lateness threshold/SLA. | Traceable scheduler/queue/dependency events show which specific mechanism delayed start, with matching run/time window and a verified causal chain or controlled reproduction. | No declared threshold, incomparable/missing timestamps, or clock skew blocks even a delay conclusion. Late completion alone does not prove late start. Missing queue/dependency evidence leaves cause unconfirmed. Evidence that run admission was on time or competing delay causes remain contradictory blocks confirmation. |
| `duplicate_data` | Record/key-level evidence demonstrates repeated business keys in the same applicable scope, or a source's validated duplicate-check result. Row excess alone is not duplicate proof. | Traceable lineage/attempt records or reproduction links the repeated records to a specific cause (for example, replay/retry plus missing idempotency, or duplicate source delivery); reconcile key scope and target writes. | If duplicate keys are valid by business rules, the comparison scope differs, or deduplication is expected, the proposed duplicate symptom/cause is disqualified. Missing keys/lineage or competing ingestion paths leaves cause unconfirmed; contradictory attempt/source records block confirmation. |
| `timeout` | Source reports a timeout/cancel tied to a configured execution limit, with run/query identity and relevant time/duration. | Query/run telemetry identifies a mechanism that led to the limit (for example, lock wait, resource saturation, or a verified plan/regression), and a controlled reproduction or causal trace connects it to this timeout. | Manual cancellation, orchestration shutdown, or another terminal event before the limit disqualifies a timeout-cause claim unless reconciled. Missing limit/telemetry leaves the cause unconfirmed. Conflicting cancellation reason or timing blocks confirmation. A timeout symptom does not by itself confirm resource exhaustion. |
| `schema_mismatch` | Validator or source/target metadata identifies the same field and incompatible type/format at the failed run. | Versioned schema/deployment/producer or mapping records show what changed and when; evidence links that change to the validator rejection and affected records. | A malformed value under an unchanged compatible schema may be a data-quality issue, not schema mismatch. Missing contemporaneous schema/version or ambiguous field mapping leaves cause unconfirmed. Conflicting schema snapshots block confirmation. |
| `dependency_failure` | Declared dependency/lineage plus source evidence that the required upstream task/artifact/service was unavailable or failed at the relevant time. | Upstream evidence identifies the specific causal failure and downstream logs/state show the dependent run was blocked by that failure; verify ordering and dependency configuration. | If the dependency was optional/not required, was available before use, or the downstream failure preceded it, that hypothesis is disqualified. Missing upstream identity/state or downstream linkage leaves cause unconfirmed. Conflicting run/time records block confirmation. |
| `early_termination` | Run/process state or completion marker shows the run ended before its expected completion state. | A source event (exit code/signal, orchestrator action, resource event, or operator action) identifies the termination mechanism and is linked to the run; verify no normal completion path. | Planned early stop, successful completion, or a completion marker before the reported termination disqualifies the cause claim unless reconciled. Missing termination reason leaves cause unconfirmed. Conflicting terminal events block confirmation. A timeout can be the cause only when timeout evidence independently passes its criteria. |
| `incomplete_data` | Comparable expected/actual counts or validator/source records establish a shortfall for the same entity, scope, and cutoff. | Source-to-target lineage, reject/filter records, transport/load evidence, or controlled reproduction accounts for the missing records and links a specific mechanism to the shortfall; reconcile counts. | Different count windows/scopes, legitimate filters, an invalid expected count, or data not yet beyond its freshness watermark disqualifies a shortfall/cause claim. Missing reconciliation leaves cause unconfirmed. Contradictory count sources or unexplained residual rows block confirmation. |

For every class, missing mandatory data, an unresolvable reference, or a
material unresolved contradiction means **do not confirm**. Preserve both
sides of conflicts; request evidence or leave the candidate unconfirmed.
Category evidence alone, correlation, temporal proximity, a log keyword, or
reviewer preference is insufficient causal proof. A reviewer may reject a
candidate even when the symptom class remains supported.

## Evaluator acceptance criteria

Future evaluator versions must report per-case pass/fail and failing case IDs.
A missing, unverifiable, or unreviewed criterion is a failure, not a pass.
Frozen evaluator v2.0 and historical reports remain untouched.

| Check | Pass condition | Fail condition |
|---|---|---|
| Evidence provenance and relevance | Every emitted evidence ref resolves exactly to a real item in that case's input evidence; the item's text/typed fields support the linked signal, candidate, conflict, or confirmation assertion. Derived signals cite every operand and recompute to the reported value. | Missing, generated-only, invented, dangling, or irrelevant ref; unsupported assertion; or unreproducible derivation. A populated reference field alone never passes. |
| Causal claim safety | Every causal statement is marked candidate or confirmed. Candidates cite supporting and, when present, contradicting evidence. A confirmed cause has the complete confirmation record and passes every predeclared criterion. Human review adjudicates claim-to-evidence relevance. | Unqualified causal statement, candidate without support, confirmation without all gates, or human approval used to override insufficient/contradictory evidence. |
| Role-based confirmation | For each confirmed cause, an investigator submission is followed by a decision from an explicitly authorized reviewer; the record contains decision, rationale, reviewer identity/role, timestamp, checklist version, and criterion-level results. The proposed independent-reviewer safeguard is met. | Classifier/LLM confirmation, missing/unauthorized reviewer, missing audit record, self-approval if independence is approved, or reviewer override of a failed/missing/contradicted criterion. |
| Cause-specific verification | Every confirmed cause maps to a supported class and satisfies all applicable positive-evidence requirements in the verification table, with source-backed evidence for the mechanism and no active disqualifier. | Symptom-only evidence is used as causal proof; a required check is missing; a disqualifier applies; or an unresolved contradiction remains. Candidate/unconfirmed outcomes may still pass when confirmation is correctly withheld. |
| Conflict | For annotated incompatible claims over the same entity/run, metric/state, and time scope, output marks evidence conflicting and cites both sides. If category choice is blocked, `classification.status=unresolved`, `resolution_status=unresolved`, and legacy category is `conflicting_evidence`. Non-comparable claims remain non-conflicts. | One side silently selected, conflict omitted, only one side cited, or non-comparable claims treated as contradictory. |
| Abstention and candidate-only | Annotated insufficient/materially ambiguous cases have `classification.status=unresolved` and `resolution_status=unresolved` with a case-specific reason. A supported symptom with unconfirmed cause has `classification.status=supported` and `resolution_status=candidate_only`, including when `candidates=[]`; in that empty case an explicit no-supported-cause explanation is present. | Category assigned without positive evidence; supported symptom marked unresolved solely because cause is unknown; empty candidate list filled with speculation; or unsupported symptom marked candidate-only. |
| Concept separation | Evidence assessment, classification, causal assessment, and lifecycle are emitted and scored independently. `candidate_only` never implies lifecycle resolution. Root-cause confirmation never follows automatically from category/candidate/LLM output. | Any state inferred from another dimension without its own evidence/transition, or incident marked solved/closed solely from classifier status. |
| Backward compatibility | Contract checks exercise the existing function tuple and API endpoints; legacy fields remain available with their existing types. Representative supported, unresolved, and conflicting cases match the mapping above. `candidates_only` remains the legacy candidate-list alias while canonical status follows both classification and causal confirmation. | Existing caller fails, legacy key/type disappears or silently changes, or legacy/canonical mapping contradicts this document. Any breaking change needs separately versioned API approval. |

Evaluator v2.0's `evidence_traceable` only compares reference and log counts;
`causation_claimed` is hard-coded false. Neither is semantic validation. The
new checks need case annotations for supported evidence links, conflict
relations, expected abstention, causal claims, and lifecycle; claims that
cannot be validated mechanically require independent human adjudication.
Because the current classifier does not receive source references, strict
traceability requires stable references at the future input boundary.

## Decision log

- **Approved:** deterministic classifier remains primary; no automatic repair;
  keep frozen reviewer holdout and historical assets unchanged.
- **Approved:** preserve `conflicting_evidence` in the legacy category while
  separating conflict from symptom in the canonical model.
- **Approved:** `candidate_only` means supported symptom/category with no
  confirmed cause; it does not mean solved and does not require a causal
  candidate.
- **Approved:** human confirmation cannot bypass predefined criteria or
  insufficient/contradictory evidence; classifier and LLM cannot promote
  candidates.
- **Proposed policy awaiting final approval:** investigator-submitted
  hypothesis, explicitly authorized human reviewer, proposed reviewer
  independence, auditable decision/rationale/identity/timestamp, and
  cause-specific positive evidence and disqualifier criteria for every
  supported class. These criteria are not empirically validated and must be
  approved before implementation or use in a human study.
- **Compatibility behavior recorded:** canonical `resolution_status`
  (`candidate_only`, `unresolved`, or `confirmed`) is derived from separate
  classification and causal-assessment fields; legacy `candidates_only`
  remains based on a non-empty candidate list until consumers migrate.

No public-data development corpus has been started. This addendum is returned
for approval; stop here until approved.
