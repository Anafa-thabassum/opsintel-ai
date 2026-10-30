# Public data provenance and label policy

The versioned source registry is
[`evaluation/public_source_registry_v1.json`](../evaluation/public_source_registry_v1.json).
Each cached row records repository, issue number, canonical source URL, source
creation and update timestamps, collection timestamp, excerpt origin (title or
body line), source-body SHA-256, code licence URL, and issue-text licence
status. The original issue remains the authoritative record; cached text is
only a screened excerpt.

The ten records came from official GitHub issue API responses for Apache
Airflow and dbt. Source code is Apache-2.0 in both repositories. GitHub issue
text is user-generated and has no separately established redistribution
licence here. The project therefore does not package full issue bodies or
external logs. GitHub's [terms](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
and [issue API](https://docs.github.com/en/rest/issues/issues) govern access;
they do not make a project-authored label an independent review.

`project_label` is mapped from the pre-existing
`evaluation/public_failure_corpus_v2.csv`, which is a project-authored
compatibility corpus. `label_status=project_assigned_unreviewed` makes this
visible in Exasol and the UI. It is not an independently adjudicated cause,
and some mappings are broader than the classifier's pipeline taxonomy. In
particular, `ModuleNotFoundError` may reflect a missing Python package rather
than a failed required upstream pipeline dependency. The current comparison
is therefore descriptive, not an independent accuracy estimate. The frozen
19-case holdout and approved development corpus V2 are unchanged and separate.

The public issue mode stores no verified root cause. Text-neighbour matches
are explicitly unverified candidates. A source describing a workaround or
closed issue does not satisfy the approved authorized-reviewer process.
