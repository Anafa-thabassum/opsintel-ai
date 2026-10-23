# Three-minute demo script

Target duration: **2 minutes 50 seconds**, leaving ten seconds of upload margin.
Use the current application with synthetic data. Do not show a database reset,
claim a repair, or enable the optional LLM unless a separate live request has
been authorized.

## 0:00-0:25 — Problem and introduction

Show the title, then move directly to the dashboard.

> At 3:07 a.m., a pipeline alert says failed, but the on-call engineer still
> has to explain why a run expected 100 rows and received 80. Run metadata,
> counts, and logs are scattered. OpsIntel brings that evidence together while
> refusing to name an unverified root cause. Uptime Institute reports that 54%
> of surveyed significant outages cost more than $100,000, but OpsIntel's impact
> study is pending, so no project-specific saving is claimed.

## 0:25-0:50 — Reproducible incident

Point to the synthetic-data label, Exasol connection indicator, trend, and
incident table. Select `daily_sales_import`.

> These are synthetic incidents stored and analysed in Exasol. The dashboard
> is not hardcoded: SQL calculates completeness and historical features. I am
> selecting the reproducible daily-sales failure, where 100 rows were expected
> and 80 arrived.

## 0:50-1:40 — Evidence, candidates, and cascade

Move left to right through observations, candidates, and the unconfirmed state.
Point to source IDs, timestamps, the last-success comparison, and the next
action. Do not imply that marking evidence as reviewed confirms a cause.

> OpsIntel retrieves the run and logs, then applies deterministic rules. Each
> observation names its source. Early termination is a candidate explanation,
> while the confirmed root cause remains empty. The engineer receives the next
> diagnostic check; no repair runs automatically.

Open the cascade panel.

> Exasol traverses the dependency graph. The failed customer-sync run is
> temporally correlated with three downstream failures that occur after it and
> within a 120-minute window. Timestamps and non-negative lag support the
> investigation, but temporal correlation does not establish causation.

If time permits, select `partner_feed` and show that unfamiliar evidence stays
unresolved instead of being forced into a confident category.

## 1:40-2:10 — Safe next steps and limitations

> The next action is diagnostic: inspect the first termination error and source
> counts before deciding whether to rerun anything. Optional model text cannot
> alter the deterministic category or confirm a cause. External-reviewer
> validation, the 40-trial human study, and live-model grounding have not been
> completed.

## 2:10-2:40 — Why Exasol and measured results

Show the architecture or `sql/analysis/pipeline_health_features.sql`, then the
evaluation slide.

> Exasol is the shared analytical evidence layer. Window functions calculate
> previous status, rolling row-count baselines, completeness, and failure rate;
> CONNECT BY traverses dependencies. The repository has 137 passing automated
> tests and 16 of 16 predefined synthetic regression cases. A licensed public
> message corpus matched 6 of 9 project-labelled cases, and every miss is
> published. In the
> cache-off comparison, DuckDB was faster on this laptop, so no Exasol speed
> advantage is claimed.

## 2:40-3:00 — Close

End on the repository URL and closing slide.

> OpsIntel places the failed run, source-backed observations, candidate
> explanations, and next safe check in one view. It does not claim production
> accuracy, measured time savings, causal cascade detection, or automatic
> recovery. Follow the evidence. Investigate faster. Confirm carefully.

## Recording checklist

- Record at 1080p with browser zoom between 90% and 100%.
- Hide notifications, bookmarks, passwords, credentials, and unrelated tabs.
- Use one continuous cursor path and pause briefly after each click.
- Keep the synthetic-data label visible when incident values are shown.
- Do not run `make smoke` while recording; it resets the synthetic schema.
- Export MP4, verify audio and scenes, and keep the duration below three minutes.
- Run `make submission-check` after replacing the existing draft video.
