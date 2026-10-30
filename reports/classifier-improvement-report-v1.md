# Classifier improvement report v1

**Classifier:** `deterministic-signals-v2`  
**Status:** implementation complete for Priority 1 review; root-cause confirmation remains human-only.  
**Evaluation warning:** the reviewer set was run once with the existing scoring function, but the evaluator's classifier-version lock was bypassed in memory. This is a development comparison, not a newly frozen or clean independent validation.

## Summary

The deterministic classifier now normalizes structured evidence, extracts typed and text-derived symptom signals, retains multiple supported symptoms, detects several scoped conflicts, and abstains canonically when evidence conflicts or does not support a category. Raw evidence and supplied references are retained. The classifier never confirms a root cause.

The historical independent-reviewer baseline remains **4/19 (21.1%)**. The revised classifier produced **15/19 (78.9%)** exact category matches under the same evaluator scoring rules, an observed increase of 11 cases (+57.8 percentage points). The original frozen dataset and historical report were not changed. This comparison alone does not establish generalization: the same reviewer set underlies the historical baseline, and the evaluator's normal guard correctly refuses to describe a changed classifier as the version frozen with that set.

## Evaluation method and integrity

- The existing `scripts/evaluate_holdout.py` scoring code was used unchanged.
- Before execution, the independent dataset hash matched the published frozen hash `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b`; the evaluator hash matched `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75`.
- Because its version guard requires the original classifier hash, that guard alone was replaced in process memory for this one run. No evaluator, dataset, historical report, or result artifact was modified. The run did not claim frozen-ref validation for the new classifier.
- Aggregate metrics were recorded; no case-level reviewer labels were used to revise rules after the run.
- The existing evaluator labels every non-`unclassified` category as `candidate_only`. Canonical OpsIntel output now labels `conflicting_evidence` as `unresolved`; therefore the evaluator's legacy unresolved count does not include every canonical unresolved outcome. Evaluation logic was preserved as requested; this semantic mismatch is a known limitation.

## Before and after

| Metric | Historical baseline | `deterministic-signals-v2` run |
|---|---:|---:|
| Exact category matches | 4/19 | 15/19 |
| Exact category accuracy | 21.1% | 78.9% |
| Legacy evaluator `unclassified` predictions | 16 | 5 |
| Complete evidence-reference cases | historical report not scored here | 19/19 |
| Outputs without a confirmed-cause claim | historical report not scored here | 19/19 |

The last two checks reflect evaluator metadata and do not prove each cited reference is semantically relevant or that every candidate is adequately supported.

### Per-category exact matches

| Expected category | Correct | Total |
|---|---:|---:|
| `conflicting_evidence` | 1 | 2 |
| `delayed_run` | 1 | 1 |
| `dependency_failure` | 3 | 3 |
| `duplicate_data` | 1 | 1 |
| `early_termination` | 2 | 2 |
| `incomplete_data` | 2 | 3 |
| `schema_mismatch` | 2 | 3 |
| `timeout` | 2 | 3 |
| `unclassified` | 1 | 1 |

These are small category counts. No precision/recall or production performance claim is made.

## Public development corpus V2

The unchanged two-case V2 corpus was exercised by the new regression test. Both cases matched their recorded development labels and status: the Cloudflare case maps to provisional `duplicate_data` / `candidate_only`; the Slack taxonomy-boundary case maps to legacy `unclassified` / canonical `unresolved`. This is a two-case development check, not an accuracy estimate or independent evaluation. The corpus's documented source/license and domain-fit limitations still apply.

## Verification

The complete existing Python test suite passed: **159 passed**. It covers input normalization and malformed values, varied signal forms, negation, multiple symptoms, evidence conflicts and source references, abstention, legacy API behavior, and V2 development labels/status. The holdout regression test now checks that the historical report and frozen dataset remain intact; it no longer expects a changed classifier to reproduce an old classifier's outputs.

The original 15 reviewer failures were not copied into rule-specific fixtures or used to tune this version. Regression cases exercise general defect patterns and approved V2 cases, preserving the holdout as an evaluation asset. This means case-by-case attribution of the observed improvement is not claimed here.

## Remaining limitations

- The 19-case result is a one-time comparison on a dataset with a published historical baseline, not an untouched new holdout. Freeze a new independent set before making a fresh generalization claim.
- The old evaluator's uncertainty mapping is not aligned with canonical `conflicting_evidence` abstention. It remains unchanged to preserve the historical scoring contract.
- Text rules are bounded patterns; scope and negation in complex prose can still be missed. Conflict detection handles selected same-run contradictions, not all evidence provenance or temporal disputes.
- Several category labels have only one to three reviewer examples. The development corpus has two cases and incomplete category coverage.
- Cause-specific verification criteria and the authorized-review workflow are approved design policies but have not been empirically validated or implemented as a review product workflow.
- `assess_root_causes` remains a legacy heuristic candidate generator. It does not confirm causes; it now suppresses candidate support where a real source reference is absent. Additional causal-evidence quality work is still needed.
- No participant study was run, so this report makes no claim that investigations are faster, more accurate for engineers, or more useful in production.

## Frozen and current hashes

| Asset | SHA-256 |
|---|---|
| Independent reviewer dataset (unchanged) | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| Historical independent JSON report (unchanged, 4/19) | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| Historical independent Markdown report (unchanged) | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |
| Original evaluator (unchanged) | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| Current classifier entry point `app/investigator.py` | `a40cae9da2a6b820440e2a8ba1e51f9806c9a519f99c3f4260e77024d0c4d99f` |
| Current classifier module `app/classification.py` | `6787be4345e897db0b31959f2a62962a9178941e6d29146e13f1f6957049e14f` |
| Public development corpus V2 (unchanged) | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |

## Review gate

Priority 1 implementation and its requested evaluation artifacts are ready for review. Stop here pending review; do not proceed to Priority 2 or commit/push without approval.
