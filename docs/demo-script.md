# Three-minute demo script

Target duration: **2 minutes 45 seconds**, leaving 15 seconds of upload margin.

## 0:00-0:20 - Problem

> Overnight data pipelines fail, and the engineer on call has to join run
> metadata, row counts, and scattered logs before they can even form a useful
> hypothesis. OpsIntel AI turns that evidence into a traceable investigation.

Show the title slide, then move immediately to the live dashboard.

## 0:20-0:42 - Operational overview

> The dashboard is reading incident telemetry calculated in Exasol. The trend
> is not hardcoded: Exasol computes completeness and rolling failure features
> over pipeline history. Eleven current incidents cover the main rule outcomes.

Point to the Exasol connection indicator, trend, and incident table.

## 0:42-1:35 - Investigation

Select `daily_sales_import`.

> I select a failed run. OpsIntel retrieves the run and its logs from Exasol,
> then classifies the available evidence. It reports early termination as a
> candidate explanation, not a confirmed root cause. Every observation names
> its source table, and the next action tells the engineer what to inspect.

Point to expected versus actual rows, each evidence item, the candidate cause,
the recent-run timeline, and the “not confirmed” boundary. Point out that each
log observation includes its source ID and timestamp. Scroll to `Confirmed root
cause: None`, set the engineer review to “Evidence reviewed”, and explain that
this demo-session state does not confirm a cause or run a repair.

If the optional summarizer is enabled, point to each narrative claim and its
evidence reference. Explain that an unknown reference rejects the whole model
response, and the model cannot change the classification or confirm a cause.

Select `product_catalog`.

> A different incident is separated as a schema mismatch because the log
> names an incompatible incoming type. The same flow handles timeout,
> dependency, incomplete-data, and unknown evidence without forcing every case
> into a confident answer.

## 1:35-1:55 - Failure cascade

Show the failure-cascade panel.

> Exasol follows the dependency graph with a hierarchical query. One failed
> customer-sync run is correlated with three failed downstream pipelines, so
> the engineer can investigate shared upstream evidence before treating each
> downstream symptom separately.

## 1:55-2:25 - Why Exasol

Show `sql/analysis/pipeline_health_features.sql` or the architecture slide.

> Exasol is the analytical core. Window functions calculate previous status,
> rolling row-count baselines, completeness, and rolling failure rates. A
> reproducible local benchmark exercises the same window analytics over one
> million synthetic runs. The recorded median query was 473 milliseconds,
> with the exact script and raw measurements included in the repository.

## 2:25-2:50 - Evidence and close

> The project has 71 automated tests, a 16-case regression challenge set, and
> a separate frozen synthetic holdout with 27 of 27 correct classifications
> across all nine outcomes. The project team authored that holdout, so an
> independent reviewer result remains pending. OpsIntel puts the failed run,
> its evidence, candidate explanations, and the next safe check in one view.

End on the repository URL and QR code if one is added during editing.

## Recording checklist

- Record at 1080p with browser zoom between 90% and 100%.
- Hide notifications, bookmarks, passwords, and unrelated tabs.
- Use one continuous cursor path and pause briefly after each click.
- Do not claim a confirmed cause, production accuracy, or production scale.
- Export MP4, verify audio, and keep the final duration below three minutes.
