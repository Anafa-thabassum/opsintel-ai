# Public development corpus validation v2

**Status: revised for user review; not approved for classifier tuning or final evaluation.** This report validates the two-case public development corpus only. Both cases remain development data and are not independent evaluation examples. No holdout labels were used to create or revise their labels. No classifier/evaluator code, frozen dataset, historical report, or benchmark was modified; no tests, classifier evaluation, database operation, benchmark, or LLM call was run for this validation.

## 1. Original corpus summary

The prior seed, [`public_development_corpus_v1.jsonl`](../evaluation/public_development_corpus_v1.jsonl), contains two documented incidents, both paraphrased from CollectSEA summaries stated to be CC BY 4.0 and linked to primary postmortems. Its case-level quality was not approved:

| Case | V1 label/status | V1 issue found |
|---|---|---|
| `DEV-PUB-001` Cloudflare | `duplicate_data`, `supported`, provisional | The primary source URL had not been re-fetched in the first collection; the individual CollectSEA record page was unavailable. No primary retrieval date was recorded. |
| `DEV-PUB-002` Slack | null / `unresolved`, ambiguous | The record identified `dependency_failure` versus `unclassified` but did not settle the taxonomy mapping or make its intended development role precise. CollectSEA itself marked the summary not yet human-reviewed. |

The original frozen reviewer holdout is not part of this development corpus. Its SHA-256 remains `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b`; the published exact-category baseline remains **4/19 (21.1%)**. Frozen classifier, evaluator, and historical report hashes also remain unchanged (listed in §8). No new evaluation was run in this corpus-validation phase.

## 2. Cloudflare source verification

**Authoritative source:** [Cloudflare outage postmortem, November 18, 2025](https://blog.cloudflare.com/18-november-2025-outage/). The page was re-opened successfully on **2026-10-30**. Its incident summary states that a database permission change resulted in repeated entries in a generated Bot Management feature file, whose size doubled and exceeded a consuming software limit. In the detailed query section, Cloudflare explains that metadata rows from another database scope were returned as duplicates; the larger output exceeded the feature limit and resulted in proxy errors. The accessible official postmortem therefore supports the **duplicate-row symptom** label. It attributes the incident mechanism, but OpsIntel has not run its authorized-review confirmation workflow, so the cause remains source-reported only. [Cloudflare incident summary](https://blog.cloudflare.com/18-november-2025-outage/), [Cloudflare query and feature-row explanation](https://blog.cloudflare.com/18-november-2025-outage/).

The original source URL is preserved in v2 and the primary retrieval date is recorded in the case. The original URL is accessible and the cited section names make the observation reproducible. The linked licensed dataset record `SEA-POST-005` still returned a cache miss on 2026-10-30; its summary is visible in CollectSEA's public homepage listing and its record ID is retained. This is a remaining gap in the curated-record metadata—not in access to the authoritative Cloudflare postmortem. The dataset page states that CollectSEA summaries, classifications, and safeguards are CC BY 4.0 and requests attribution; the linked publisher article has not been assigned a reuse license by this project. V2 contains short paraphrases, attribution, links, and no copied primary-source text. [CollectSEA license and attribution terms](https://collectsea.com/dataset).

**Taxonomy result:** `duplicate_data` is defensible as a direct symptom label because the authoritative source explicitly reports duplicate generated feature rows. Scope is limited: this is a data-adjacent configuration-generation artifact, not a conventional ETL/business-key incident. The approved cause-specific policy's stronger verification criteria are not asserted to have been met; the root cause is not OpsIntel-confirmed. Keep the label provisional pending independent corpus review, and do not represent this as a pipeline-specific example without that reviewer accepting the cross-domain fit.

**Missing/contradictory evidence:** No contradictory account was found in the reviewed postmortem. The evidence does not establish duplicate business keys in a customer table, source-to-target lineage, or a conventional pipeline run. Those absences limit transfer to OpsIntel's target domain, not the report's direct duplicate-feature-row observation.

## 3. Slack taxonomy resolution

**Authoritative source:** [Slack Engineering postmortem for January 4, 2021](https://slack.engineering/slacks-outage-on-january-4th-2021/). The first-party page was accessible and re-opened on **2026-10-30**. Slack describes degraded network connectivity and packet loss, higher latency to backend dependencies, provisioning-service resource limits, an exceeded cloud quota, and many new instances that were not fully provisioned. CollectSEA's [SEA-POST-022 summary](https://collectsea.com/incidents/SEA-POST-022) was also accessible; it identifies itself as a documented incident and says it is **not yet human-reviewed**. The primary postmortem was independently read and cross-checked, so the incident facts are not accepted solely on CollectSEA's unreviewed annotation. [Slack postmortem details](https://slack.engineering/slacks-outage-on-january-4th-2021/).

**Taxonomy comparison and resolution:** OpsIntel's `dependency_failure` is a pipeline symptom category: evidence should identify a required upstream task, artifact, or service that failed or was unavailable in relation to the affected run. Slack's systems did rely on internal services and cloud APIs, and their latency contributed to a provisioning cascade. But the incident is a web-tier/network/autoscaling outage, not a data-pipeline run or pipeline dependency failure. Calling it a positive `dependency_failure` training case would collapse a causal dependency/network mechanism into an OpsIntel pipeline symptom category. V2 therefore records canonical `classification.status=unresolved`, null symptom category, and legacy `category=unclassified`, with `dependency_failure` explicitly retained as a considered but rejected positive label. It is a **development taxonomy-boundary/abstention example only**, pending independent reviewer agreement—not an independent test case and not a positive category label.

**Missing/contradictory evidence:** The reviewed sources provide a detailed account and no competing account was found. They do not provide a data-pipeline run, data artifact, expected/actual data counts, or pipeline lineage. Multiple interacting infrastructure mechanisms are present; v2 does not select one as an OpsIntel root cause. This label is an explicit out-of-domain decision, not uncertainty about whether the Slack outage happened.

## 4. Case-by-case corpus validation

| V2 case | Authenticity and access | Evidence completeness | Expected label and taxonomy consistency | Duplicates/conflicts | Reproducibility / disposition |
|---|---|---|---|---|---|
| `DEV-PUB-001` Cloudflare | First-party Cloudflare postmortem accessible on 2026-10-30. CollectSEA homepage summary accessible; individual `SEA-POST-005` page still cache-misses. Licensed summary terms and attribution verified at dataset page. | Duplicate feature rows, changed output size, runtime limit, and impact are supported. No data-pipeline run ID, business-key evidence, or source-to-target lineage. No contrary evidence found in the reviewed postmortem. | `duplicate_data` / `supported` is defensible for the observed artifact symptom, but cross-domain fit is provisional. `candidate_only`; cause not confirmed by OpsIntel. | No duplicate corpus incident. No conflicting source claim found. | Primary URL, retrieval date, titled sections, and CollectSEA record ID retained. Development positive, **not final evaluation**; tuning only after independent label/provenance review accepts domain fit. |
| `DEV-PUB-002` Slack | First-party Slack postmortem and CollectSEA record accessible on 2026-10-30. CollectSEA record explicitly not human-reviewed; source independently checked. | Network, dependency latency, provisioning limits, quota, and incomplete instance provisioning are documented. No pipeline run/artifact/lineage evidence. No competing incident account found. | Canonical `unresolved`, legacy `unclassified`; `dependency_failure` is not accepted as a positive OpsIntel symptom label because this is outside the data-pipeline scope. | No duplicate corpus incident. Several interacting mechanisms are evidence, not contradictory reports. | Source URLs, date, and section locators retained. Development abstention/taxonomy-boundary example, **not final evaluation**; reviewer should confirm the domain boundary before its use. |

Neither record has been independently label-adjudicated by a second OpsIntel reviewer yet. These are provisional corpus labels, not ground truth. V2 includes no negative class claim that the incident did not occur.

## 5. Taxonomy definitions

No approved taxonomy definition is changed in this revision. For consistent use in this corpus:

- `duplicate_data` describes observed repeated records/rows in an artifact. The Cloudflare case qualifies at symptom level because the source explicitly identifies duplicate feature rows. Its cross-domain fit remains provisional; row excess by itself would not prove duplication.
- `dependency_failure` describes a supported data-pipeline symptom tied to a required upstream task, artifact, or service and relevant run. A dependency mechanism in an unrelated infrastructure outage does not automatically meet that category.
- `unresolved` is the canonical status when the evidence does not support a defensible supported symptom category or a material scope ambiguity remains. For legacy compatibility, this Slack record maps to `unclassified`.
- `candidate_only` means the symptom is supported but no root cause is confirmed. Neither record's lifecycle is inferred. Source-reported mechanism is not OpsIntel confirmation.

The approved role-based reviewer policy and seven cause-specific confirmation criteria remain design policies; they are **not empirically validated** and are not claimed as passed by either record.

## 6. Additions, removals, and corrections

- **Additions:** none. V2 adds no new incident beyond the two v1 cases.
- **Removals:** none from the audit trail. Both cases remain in v2, with their role and eligibility clarified.
- **Cloudflare correction:** preserved the original primary-source URL; re-fetched the accessible official postmortem on 2026-10-30; added reproducible section locators and retrieval date; replaced the unresolved primary-source access claim with a precise distinction between accessible Cloudflare evidence and inaccessible individual CollectSEA record page; documented domain-fit caveat and made tuning conditional on reviewer approval.
- **Slack correction:** re-fetched the first-party postmortem on 2026-10-30; compared it with the pipeline-specific dependency definition; resolved the prior vague ambiguity into a canonical `unresolved` / legacy `unclassified` out-of-domain label; documented why it is not a positive `dependency_failure` example; retained as an abstention-boundary development case.
- **Evaluation separation:** v2 records `dataset_role` for each case. Both are development examples only. No new independent evaluation set has been created, and neither case may be described as an independent result. The frozen 19-case holdout remains separate and unchanged.

## 7. Provenance, licensing, and data-quality requirements

V2 stores fact paraphrases and source locators, not copied logs or postmortem passages. For both cases, the reused curated summary is attributed to CollectSEA under its stated CC BY 4.0 terms; the primary publishers' licensing terms were not separately assessed. The primary URLs are linked as authoritative factual sources. The record metadata includes source identity, event-date basis, retrieval date, locator, snapshot, license URL, attribution, and any access/review limitation.

Quality checks applied: source publisher and identity; live accessibility on the retrieval date; agreement of public summary with primary report; incident-date basis; symptom-versus-cause separation; category fit; alternatives and missing metadata; duplicate/conflicting record check; role separation; and retention of the source URLs and stable record IDs. These are manual source checks, not a classifier evaluation.

## 8. Dataset hashes and evaluation integrity

SHA-256 values calculated during this validation:

| Asset | SHA-256 |
|---|---|
| Original seed `evaluation/public_development_corpus_v1.jsonl` (unchanged) | `f2937bf8f842f61a77432c41a61351d7d70b4c314e70e4d212fc118a1dcfaf58` |
| Revised development corpus `evaluation/public_development_corpus_v2.jsonl` | `2b16264d2954e57f9202dc3d9fa2e00e04d466598748caeb31e158381c331a5e` |
| Frozen independent holdout `evaluation/independent_holdout_v1.csv` (unchanged) | `64d766d4782ee94223796e91d79c35fb359d3dcd9de414b1b8ebed41afacf71b` |
| Frozen classifier `app/investigator.py` (unchanged) | `bc274d54f8f161a2f56388118742ae4dee44a0717687b5caab246fa7467d1c10` |
| Frozen evaluator `scripts/evaluate_holdout.py` (unchanged) | `c07b1f2ddcc3b5e1f11447bf8f7aa98501c2f99c5d8f3657106945254d9feb75` |
| Historical independent result `reports/independent-holdout-v1.json` (unchanged) | `79b54ba0825313089ed44b13d9ae87c7f3edcbbc5186658ed6a240fc9001235a` |
| Historical independent report `reports/independent-holdout-v1.md` (unchanged) | `6a9e58bc1322e591eb8bbe43e630c57bebd762c3f45c2bdc35b70de5598824c2` |

The original independent baseline remains **4/19 (21.1%)**, as recorded in the frozen report and reproduced during the preceding audit. Corpus validation did not rerun that evaluation, change its labels, tune against its cases, or generate new performance claims. No report/result outputs were written by an evaluator in this phase.

## 9. Remaining limitations

- Only two cases; one provisional cross-domain duplicate-artifact symptom and one out-of-domain abstention case. This is not enough to tune or evaluate generalization.
- Both cases come from the same curated dataset family, creating editorial/source bias.
- The Cloudflare individual CollectSEA record page remains inaccessible during retrieval; its licensed summary was available on the public listing, and the authoritative first-party postmortem is accessible.
- The primary publishers' license terms were not separately assessed. No primary-source prose is reproduced; v2 relies on paraphrase of the CollectSEA material under its stated CC BY 4.0 license and attributes it.
- No second human reviewer has adjudicated case labels or scope. Cloudflare's cross-domain `duplicate_data` mapping and Slack's out-of-domain `unclassified` mapping need user/reviewer sign-off before use for tuning.
- There are no public development examples for the other supported categories, no adjudicated conflict pair, no controlled negative set, and no independent new holdout. Nothing in this corpus validates the cause-confirmation policy or user benefit.

## 10. Final approval recommendation

**Recommend conditional approval as a small, source-traceable development seed only**, after an independent reviewer agrees that (a) the Cloudflare duplicate-feature-row symptom is in scope for `duplicate_data`, and (b) Slack should remain an out-of-domain abstention case. Do not use v2 for final evaluation, claim generalization, or tune classifier rules until that review and explicit user approval occur. The Cloudflare primary evidence is now accessible and reproducible; the Slack taxonomy decision is documented rather than forced into a positive class.

**Implementation gate remains closed.** No classifier/evaluator code, frozen evaluation asset, or historical result has been modified. Wait for the user's explicit approval of this revised corpus and its quality before beginning Priority 1 implementation.
