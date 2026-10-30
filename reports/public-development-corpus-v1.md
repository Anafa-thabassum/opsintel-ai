# Public development corpus v1: methodology and collection record

**Status: collected seed corpus, pending human quality review.** This is a
separate, versioned development artifact. It does not change or replace any
existing synthetic or public evaluation corpus, the frozen 19-case reviewer
holdout, historical reports, or submission assets. No classifier/evaluator
code was changed, and no tests, evaluations, database operations, benchmarks,
or live LLM calls were run. No classifier implementation is authorized by this
work.

The authorized-reviewer confirmation policy and seven cause-specific
verification criteria are approved design policies, but **have not been
empirically validated**. This corpus does not validate those policies or
confirm a root cause in OpsIntel.

## Proposed corpus schema

The data file is [`evaluation/public_development_corpus_v1.jsonl`](../evaluation/public_development_corpus_v1.jsonl), one JSON object per incident. This schema is proposed for future versions; v1 is intentionally a small, reviewable seed rather than a training-ready benchmark.

| Field | Meaning and constraint |
|---|---|
| `dataset_version`, `case_id`, `case_type` | Stable version and unique case identity; only documented public incidents are included in v1. |
| `incident_date`, `incident_date_basis` | Publicly stated event date and what the date represents; do not infer an exact time when sources do not provide one. |
| `incident_summary` | Short paraphrase; no copied log, issue, or postmortem passages. |
| `evidence_items[]` | Source-backed observations with stable reference, evidence kind, event time when available, locator, source URL, and primary-source URL/locator. A reference is valid only because it resolves through these provenance fields; the identifier alone is not proof. |
| `evidence_assessment` | Sufficiency/conflict assessment for the observations, separate from classification and cause. |
| `classification` | OpsIntel symptom category or null, supported/unresolved state, label status, rationale, and considered alternatives where ambiguous. The legacy `conflicting_evidence` category is not used as a symptom label. |
| `causal_assessment` | Source-reported or independently proposed candidates with evidence references; `confirmed_root_cause` stays null unless the approved reviewer workflow is separately completed. |
| `resolution_status`, `incident_lifecycle` | Decision summary and lifecycle are independent. `candidate_only` never means solved; lifecycle is not inferred by this dataset. |
| `labeling` | Rationale, reviewer/adjudication status, confidence by claim, and whether a case is eligible for rule tuning. |
| `provenance` | Dataset and record identity, snapshot, license, attribution, primary publisher/link, primary-source license status, content basis, and changes. |

## Source and licensing requirements

For inclusion, a source must meet all of the following:

1. Be a public, source-linked documented incident or primary postmortem—not a
   synthetic scenario, advisory, benchmark-generated sample, or existing
   OpsIntel evaluation case.
2. Provide a stable record identifier, record URL, primary-source URL, event
   date basis, and enough locators to independently find each relied-on fact.
3. Have an explicit license permitting reuse of the corpus material. Record
   the license URL and required attribution. “Publicly accessible” alone is
   not treated as a reuse license.
4. Keep source layers distinct. If the reusable license covers a curated
   summary but not the primary article, retain only a paraphrase of the
   licensed summary, link the primary article for verification, and do not
   reproduce primary-source wording.
5. Record capture/access gaps and source-reliability limitations. Exclude a
   case if its essential fact or reuse permission cannot be traced.

V1 uses the CollectSEA dataset. Its dataset page states that its summaries,
classifications, and safeguards are CC BY 4.0, requests attribution to
“CollectSEA (collectsea.com),” and distinguishes that licensed material from
original publisher sources, whose terms remain separate. Accordingly, these
records paraphrase the licensed summaries, credit CollectSEA, link the original
postmortems, and do not reproduce their text. The [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/) requires appropriate credit, a license link, and an indication of changes. This documentation is a provenance record, not legal advice.

Source register:

| Case | Licensed record | Primary source | License treatment |
|---|---|---|---|
| `DEV-PUB-001` | [CollectSEA SEA-POST-005](https://collectsea.com/incidents/SEA-POST-005), snapshot `2026.10.26`; listing also visible on the [CollectSEA homepage](https://collectsea.com/) | [Cloudflare November 18, 2025 postmortem](https://blog.cloudflare.com/18-november-2025-outage/) | CC BY 4.0 applies to the CollectSEA summary. Primary article license not separately assessed; no primary text copied. The individual record URL returned a cache miss during collection, noted in the case record. |
| `DEV-PUB-002` | [CollectSEA SEA-POST-022](https://collectsea.com/incidents/SEA-POST-022), snapshot `2026.10.26` | [Slack January 4, 2021 postmortem](https://slack.engineering/slacks-outage-on-january-4th-2021/) | CC BY 4.0 applies to the CollectSEA summary. Primary article license not separately assessed; no primary text copied. |

## Labeling guidelines

- Assign only the operational symptom category supported by the actual
  observation. Do not promote an inferred mechanism into a symptom label.
- Distinguish symptom evidence from causal evidence. A source's own attribution
  may be preserved as `source_reported_hypothesis`, but it is not an OpsIntel
  `confirmed_root_cause`.
- `candidate_only` means supported symptom, no OpsIntel-confirmed cause; it
  does not mean resolved. Empty causal candidate lists are valid if no
  hypothesis is adequately supported.
- Use `unresolved` when evidence does not support a defensible category or a
  material taxonomy/label ambiguity remains. Explain alternatives and do not
  force a category.
- Preserve both sides of any material conflict. No conflict is fabricated in
  these two cases.
- Mark label confidence and adjudication state; do not present provisional
  curator labels as ground truth.
- Root-cause confirmation would require the approved role-based review,
  criterion-by-criterion verification, traceable support, reviewer identity,
  rationale, and timestamp. This corpus has no such OpsIntel confirmation
  record. The seven cause-specific criteria remain design policies and are
  not empirically validated.
- Do not use the existing frozen reviewer cases or historical evaluation
  labels to tune or revise these labels, category definitions, or rules.

## Collection methodology

1. Select documented incidents from the licensed source's documented-incident
   tier; exclude advisories, illustrative scenarios, and synthetic-looking
   records.
2. Check the dataset license and attribution terms before recording case
   content. Snapshot the dataset version/date and record the individual
   identifier and URL.
3. Locate the linked primary report and independently verify the paraphrased
   observations, incident date, and relevant section. Store locators, not
   copied passages.
4. Write symptom labels independently against the existing OpsIntel
   taxonomy. Record considered alternatives and reasons for abstention.
5. Separate source-attributed causal explanation from OpsIntel confirmation.
   Never fill the `confirmed_root_cause` field from a postmortem alone.
6. Mark each case as eligible or ineligible for future rule tuning. Ambiguous
   cases remain quarantined until human adjudication.
7. Preserve the resulting JSONL and methodology report as a new version; do
   not edit existing evaluation files or historical results.

This is a manual, source-by-source collection. There was no automated
scraping, model-generated data, synthetic augmentation, classifier tuning, or
evaluation in this phase.

## Quality-control and acceptance checklist

For each case, a reviewer must verify:

- **Identity:** unique ID, documented-incident evidence tier, stable dataset
  record ID and URL, primary source, event date basis, and dataset snapshot.
- **License:** explicit license and URL for the reused material, required
  attribution, change notice, and no assumption that a linked publisher's
  page shares that license.
- **Provenance:** every evidence reference resolves to a real source item and
  locator; each observation is materially supported by the source. Generated
  labels alone fail this check.
- **Faithful paraphrase:** no copied text; no fact stronger than the source;
  attribution and source layers stay distinct.
- **Label fit:** category rationale points to symptom evidence; cause
  assessment is separate; alternatives, ambiguity, and out-of-scope conditions
  are recorded; unsupported root causes remain null.
- **Status consistency:** supported symptom with no confirmed cause is
  `candidate_only`; insufficient or materially ambiguous classification is
  `unresolved`; lifecycle is not inferred.
- **Human review:** a second reviewer independently checks label and
  provenance. Disagreements remain ambiguous pending adjudication; the curator
  does not silently resolve them.
- **Isolation:** verify that no frozen holdout, historical report, or existing
  evaluation dataset was used as a source or altered during collection.

V1 passes the basic source/license traceability gate for both records at the
dataset-summary level, with an explicit record-page access gap on
`DEV-PUB-001`. V1 has **not** passed independent human label adjudication; do
not call it a validated benchmark or use the ambiguous second case for rule
tuning.

## Collected cases and label rationale

### `DEV-PUB-001` — Cloudflare duplicate feature rows

The source reports duplicate metadata/feature rows in a generated artifact,
which supports `duplicate_data` directly. This is a symptom label; the reported
permissions/query mechanism is preserved only as a source-reported candidate.
No OpsIntel-authorized reviewer has completed the required confirmation
workflow, so `confirmed_root_cause` remains null and `resolution_status` is
`candidate_only`. The label is high-confidence at symptom level but still
awaits independent review. The individual CollectSEA record page was not
retrievable in the browser at collection time; the stable ID and summary were
visible in its homepage listing and its source links to Cloudflare's detailed
postmortem. Treat this as a recorded access limitation and independently
re-fetch before relying on it for tuning.

### `DEV-PUB-002` — Slack provisioning and capacity cascade

The source supports an infrastructure cascade involving degraded dependencies,
resource limits, quotas, and incompletely provisioned instances. One could map
part of this to `dependency_failure`, but it is not clearly a data-pipeline
symptom and multiple interacting mechanisms are present. The case is retained
as `unresolved` with `dependency_failure` and `unclassified` noted as
alternatives. It is **not eligible for rule tuning** until a second human
adjudicates scope and label. No cause is confirmed by OpsIntel.

## Exclusions, gaps, and coverage limits

- Existing `public_failure_corpus_v1.csv`, `public_failure_corpus_v2.csv`,
  synthetic datasets, reviewer holdout, and historical result assets were
  deliberately not reused or modified.
- The Cloudflare CollectSEA record URL returned a cache miss during collection.
  Its stable ID and summary were visible in the homepage incident listing, and
  the primary postmortem is available, but the individual record's detailed
  review metadata could not be independently inspected in this capture. This
  is an explicit provenance completeness gap; re-fetch and verify its current
  review status before using it for tuning.
- The primary publishers' reuse licenses were not separately assessed. Only
  CollectSEA's licensed paraphrases are represented in the corpus; primary
  pages are linked for factual verification and no wording is copied.
- Two cases are far too few to establish generalization, estimate accuracy,
  compare categories, or tune robustly. Only one has a provisional supported
  OpsIntel symptom label, and that label still requires independent review.
- Coverage is concentrated in one Cloudflare data-adjacent duplicate-artifact
  incident plus one out-of-domain/ambiguous Slack infrastructure incident.
  There are no adjudicated public examples yet for delayed runs, timeouts,
  schema mismatch, dependency failures in an actual data pipeline, early
  termination, or incomplete data; no negative, explicit-conflict, or
  insufficient-evidence collection has been validated.
- Selection from one curated dataset creates source and editorial bias. This
  is a pilot corpus only—not evidence of classifier improvement, causation
  policy validity, or user benefit.

## Decision log and next gate

- **Applied:** approved role-based cause-confirmation workflow and seven
  cause-specific criteria are treated as design policy; the corpus does not
  claim empirical validation.
- **Preserved:** existing API terminology, canonical/legacy separation,
  provenance requirements, frozen evaluation assets, and independent
  holdout. No implementation or evaluation changes.
- **Collected:** two public, documented, source-linked cases from a dataset
  whose summaries are stated to be CC BY 4.0, with attribution and links.
- **Unresolved:** `DEV-PUB-002` category/scope ambiguity; `DEV-PUB-001`
  individual record review status due cache miss; no independent reviewer has
  yet adjudicated either case.
- **Next gate:** independent human provenance/label review and, for any future
  classifier decisions, separate user approval. Stop before classifier
  implementation. Do not collect another batch or change category rules
  until the user reviews this corpus and its quality.
