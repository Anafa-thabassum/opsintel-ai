# Three-minute demo script

Target duration: **2 minutes 45 seconds**, leaving 15 seconds of upload margin.

## 60-second judge path

1. **0:00–0:10:** open the dashboard and select `daily_sales_import`.
2. **0:10–0:35:** move left to right through observed facts, candidate causes,
   and “not yet verified”; point to the next safe check.
3. **0:35–0:50:** show the Exasol cascade from `customer_sync` to three failed
   downstream runs.
4. **0:50–1:00:** select `partner_feed` and show that unfamiliar evidence stays
   “Unknown — evidence insufficient” with a useful next check.

## 0:00-0:20 - Problem

> At 3:07 a.m., a pipeline alert says “failed,” but the engineer still has to
> explain why a run expected 100 rows but received 80. They must join run
> metadata, row counts, and scattered logs before forming a useful
> hypothesis. OpsIntel turns that evidence into a traceable investigation. It
> refuses to name an unverified root cause and keeps facts separate from
> explanation. The impact study has not run yet, so no time saving is claimed.

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

> Exasol is the operational analytical core. Window functions calculate
> previous status, rolling row-count baselines, completeness, and failure
> rates; CONNECT BY traverses dependencies; and the bulk import path loads the
> synthetic benchmark. In the controlled cache-off comparison, DuckDB was
> faster on this laptop, including about 4.5 times faster at ten million rows.
> We publish that result instead of claiming an unsupported Exasol speed win.

## 2:25-2:50 - Evidence and close

> The project has 80 automated tests, a 16-case regression challenge set, and
> a separate versioned project-authored holdout with 27 of 27 correct
> classifications
> across all nine outcomes. The project team authored that holdout. The external
> holdout currently contains zero reviewer cases from zero external authors,
> and the impact study contains zero of forty trials from zero of four
> participants. OpsIntel puts the failed run, its evidence, candidate
> explanations, and the next safe check in one view.

End on the repository URL and QR code if one is added during editing.

## Recording checklist

- Record at 1080p with browser zoom between 90% and 100%.
- Hide notifications, bookmarks, passwords, and unrelated tabs.
- Use one continuous cursor path and pause briefly after each click.
- Do not claim a confirmed cause, production accuracy, or production scale.
- Export MP4, verify audio, and keep the final duration below three minutes.
