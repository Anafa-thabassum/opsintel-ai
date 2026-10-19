# Frozen synthetic holdout v1

## Result

- Correct classifications: **27/27**
- Accuracy on this dataset: **100.0%**
- Cases per expected category: **3**
- Categories covered: **9**

This is a project-authored synthetic holdout, not an independent evaluation or
a production accuracy estimate.

## Freeze evidence

| Item | Frozen value |
|---|---|
| Dataset | `evaluation/frozen_holdout_v1.csv` |
| Dataset SHA-256 | `a7da47b53b8b985238cfb4f59cfb71755a3b76a283467df125c99e46fa181f71` |
| Classifier | `app/investigator.py` |
| Classifier SHA-256 | `762eee2ad9077a1ee067e2c1276015b6a9eb4e253be1e05c8127b5abad724181` |
| Classifier commit | `eb7a2d8c2202a45603015c32e9a187de533f5a21` |

The expected labels were written into the versioned dataset before the
evaluator ran. The classifier was not changed between freezing the dataset and
recording the result. Future case changes must use a new versioned dataset
instead of editing v1.

## Category results

| Expected category | Correct | Total |
|---|---:|---:|
| Conflicting evidence | 3 | 3 |
| Delayed run | 3 | 3 |
| Dependency failure | 3 | 3 |
| Duplicate data | 3 | 3 |
| Early termination | 3 | 3 |
| Incomplete data | 3 | 3 |
| Schema mismatch | 3 | 3 |
| Timeout | 3 | 3 |
| Unclassified | 3 | 3 |
| **Total** | **27** | **27** |

## Reproduce

```bash
python -m scripts.evaluate_holdout evaluation/frozen_holdout_v1.csv
```

The machine-readable per-case output is stored in
`reports/frozen-holdout-v1.json`.

## Claim boundary

The project team authored these synthetic cases, so they may share assumptions
with the implementation. The separate empty template remains available for a
reviewer-controlled evaluation whose cases are genuinely unseen by the project
team. Neither result should be presented as real-world accuracy without a
larger independent dataset.
