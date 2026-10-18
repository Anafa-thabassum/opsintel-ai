# Three-minute demo script

Target duration: **2 minutes 45 seconds**, leaving 15 seconds of upload margin.

## 0:00-0:20 - Problem

> Overnight data pipelines fail, and the engineer on call has to join run
> metadata, row counts, and scattered logs before they can even form a useful
> hypothesis. OpsIntel AI turns that evidence into a traceable investigation.

Show the title slide, then move immediately to the live dashboard.

## 0:20-0:45 - Operational overview

> The dashboard is reading incident telemetry calculated in Exasol. The trend
> is not hardcoded: Exasol computes completeness and rolling failure features
> over pipeline history. Four current incidents are visible here.

Point to the Exasol connection indicator, trend, and incident table.

## 0:45-1:45 - Investigation

Select `daily_sales_import`.

> I select a failed run. OpsIntel retrieves the run and its logs from Exasol,
> then classifies the available evidence. It reports early termination as a
> candidate explanation, not a confirmed root cause. Every observation names
> its source table, and the next action tells the engineer what to inspect.

Point to expected versus actual rows, each evidence item, the candidate cause,
and the “not confirmed” boundary.

Select `product_catalog`.

> A different incident is separated as a schema mismatch because the log
> names an incompatible incoming type. The same flow handles timeout,
> dependency, incomplete-data, and unknown evidence without forcing every case
> into a confident answer.

## 1:45-2:20 - Why Exasol

Show `sql/analysis/pipeline_health_features.sql` or the architecture slide.

> Exasol is the analytical core. Window functions calculate previous status,
> rolling row-count baselines, completeness, and rolling failure rates. A
> reproducible local benchmark exercises the same window analytics over one
> million synthetic runs. The recorded median query was 473 milliseconds,
> with the exact script and raw measurements included in the repository.

## 2:20-2:45 - Evidence and close

> The project has 45 automated tests, a 16-case regression challenge set,
> continuous integration, a public MIT licence, and a separate protocol for a
> reviewer-controlled holdout test. OpsIntel shortens the path from “the
> pipeline failed” to “here is the evidence and the next safe check.”

End on the repository URL and QR code if one is added during editing.

## Recording checklist

- Record at 1080p with browser zoom between 90% and 100%.
- Hide notifications, bookmarks, passwords, and unrelated tabs.
- Use one continuous cursor path and pause briefly after each click.
- Do not claim a confirmed cause, production accuracy, or production scale.
- Export MP4, verify audio, and keep the final duration below three minutes.
