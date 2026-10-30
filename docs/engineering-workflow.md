# OpsIntel AI engineering workflow

This workflow keeps future changes architecture-first, evidence-based, and
small enough to review. It applies to application changes, evaluation changes,
database changes, integrations, and submission claims. It does not replace the
existing run instructions in [`README.md`](../README.md),
[`docs/deployment.md`](deployment.md), or the evaluation guidance in
[`evaluation/README.md`](../evaluation/README.md).

## 1. Clarify the requirement

Before designing a change, write down:

- the user or judge problem;
- the observable outcome that will prove it is solved;
- what is explicitly out of scope;
- the data, environment, credentials, and approval needed;
- whether the change affects runtime behavior, evaluation evidence, or
  submission claims.

Resolve ambiguous requirements before implementation. Do not turn a proposed
feature, benchmark, study protocol, or roadmap item into a completed result.

## 2. Inspect the architecture and constraints

Read the relevant implementation, tests, SQL, documentation, and current Git
state before editing. Trace the complete data flow and record affected
components:

- system architecture and data movement;
- API routes and response contracts;
- Exasol tables, views, analytical SQL, and storage boundaries;
- evidence retrieval and classification rules;
- frontend states and user-visible wording;
- security, credentials, TLS, reliability, observability, and failure modes;
- evaluation datasets, freeze points, scoring rules, and benchmark conditions;
- pitch deck, narration, video, and other submission claims.

Reuse existing helpers, scripts, tests, and documentation. Do not introduce a
new framework or duplicate an existing workflow without a demonstrated need.

## 3. Protect the non-negotiable invariants

Every change must preserve these project boundaries:

1. Exasol remains the analytical core.
2. Existing FastAPI routes and response fields remain compatible unless an
   explicitly approved migration is documented.
3. Deterministic evidence-based classification remains the primary decision
   path.
4. Observations, candidate explanations, and confirmed root causes remain
   separate.
5. Dependency cascades are temporal correlations within the existing
   120-minute window; correlation does not prove causation.
6. Unknown, conflicting, and insufficient-evidence cases remain unresolved.
7. Candidate explanations retain traceable supporting evidence.
8. The optional LLM may summarize retrieved evidence only. It must preserve
   uncertainty, reject unsupported claims, and fall back to the deterministic
   result when disabled or unavailable.
9. Frozen evaluation datasets, labels, scoring rules, benchmark measurements,
   and historical reports are not rewritten to improve a result.
10. Synthetic, public, reviewer, and participant-study data remain clearly
    separated and provenance is retained.
11. Credentials and sensitive data never enter source, logs, reports, or
    user-facing errors.
12. The application never automatically repairs, reruns, or changes an
    incident pipeline.

If a proposed change conflicts with an invariant, stop and request an explicit
architecture decision before implementation.

## 4. Propose a small scoped plan

Use [`templates/change-plan.md`](templates/change-plan.md). The plan must name
the exact files to inspect and change, the relevant contracts and invariants,
the test-first or test-before-merge strategy, external-service boundaries,
failure handling, and rollback steps.

Significant changes require human approval before implementation. Significant
means a change to application architecture, Exasol schema or SQL contracts,
API behavior, classifier semantics, LLM behavior, evaluation methodology,
benchmark methodology, security boundaries, or submission claims. A purely
clarifying documentation edit may proceed when it does not change a factual
claim.

## 5. Implement the smallest safe change

Keep the change focused. Preserve unrelated user work. Prefer existing
dependencies and standard-library mechanisms. Add tests with the change where
practical, especially for classifier rules, API contracts, evidence
validation, database safety, and evaluation scoring.

Do not run database reset, seed, import-apply, deployment, or live LLM commands
unless the user has approved the exact target, credentials, and side effects.
Use synthetic or disposable data only. Keep remote Exasol TLS verification
enabled and never print credentials.

## 6. Debug from the root cause

When a check fails:

1. Reproduce the failure with the smallest safe command.
2. Trace the failing value or contract to its source.
3. Fix the shared root cause rather than patching one caller or one artifact.
4. Add or update the smallest regression test.
5. Re-run the focused check and then the relevant full verification.

Do not weaken a checker, delete a failing case, or edit a historical result to
make validation pass.

## 7. Verify with actual evidence

Report commands exactly as run and distinguish passed, failed, skipped, and
blocked checks. Do not claim a test, benchmark, study, live Exasol workflow,
LLM evaluation, or productivity improvement that was not actually measured.

For ordinary code changes, use the relevant subset of:

```bash
python -m pytest -q
python -m tests.run_evaluation
python -m scripts.verify_submission --allow-dirty
git diff --check
cd frontend && npm run lint
cd frontend && npm run build
```

Use the repository Makefile and deployment documentation as the source of
truth for setup and live-service checks. Treat `make database`, `make smoke`,
`make impact-study-database`, Exasol benchmarks, and import commands with
`--apply` as state-changing operations requiring explicit approval.

## 8. Review, preserve, and roll back

Before handoff, review the diff, Git status, protected files, API and data
contracts, security boundaries, evaluation provenance, and submission wording.
Keep unrelated changes untouched. A documentation-only change should roll back
by reverting its documentation diff; an application change must identify the
previous behavior and the smallest recoverable rollback before merging.

The completion report must include changed files, tests and commands actually
run, unresolved limitations, external checks not performed, and the next human
decision required.
