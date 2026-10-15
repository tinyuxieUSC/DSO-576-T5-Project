# Views — Client Metadata Outreach Prioritizer

The app is for a MetaBrainz project lead deciding which active ListenBrainz
client maintainer to approach first. All views use aggregate data. They must
never display `user_id`, `user_name`, individual listens, or any other
listener-level identifier.

## Job and contract

This piece turns filtered aggregate client metrics into the four screens that
support the outreach decision. Views do not read CSV, Parquet, or raw JSON
files, and they do not calculate listener-level data. They receive aggregate
data plus plain settings and return a rendered view. A table-row or chart click
returns only a selected client name to the shared dashboard state.

| View | Receives | Returns/displays |
|---|---|---|
| Shortlist | One aggregate row per client plus date range, importer rule, minimum-account threshold, and ranking weights | Ranked table, reach/opportunity scatter plot, and optional selected client |
| Client detail | One selected client, its aggregate metrics, optional weekly aggregates, and optional version aggregates | Metric cards, coverage chart, trend chart, version table, and limitations |
| Scenario comparison | Two or three selected client summaries plus a target coverage percentage | Scenario chart, comparison table, and assumptions |
| Briefing/export | Selected client summary, active settings, scenario results, and warnings | Aggregate briefing on screen and downloadable CSV or Markdown/HTML |

The dashboard owns navigation and shared selection. A view knows only its own
input contract and display; it does not access another view's internals.

## Shared definitions

The data unit is one submitted listen. The analysis period is the selected
`listened_at_utc` playback-date range, not the daily dump's submission date.
The view layer uses these aggregate definitions:

| Measure | Definition |
|---|---|
| Total listens | Number of filtered listen rows for a client. |
| Distinct accounts | Distinct observed `user_id` values for a client; the ID is counted internally and never displayed. |
| Affected accounts | Distinct accounts with at least one listen missing a recording MBID. |
| Missing-MBID listens | Filtered listen rows without a recording MBID. |
| Recording-MBID coverage | Listens with a recording MBID divided by total listens. |
| Priority score | The shared ranking calculation using the selected reach and missing-listen weights; show the active weights. |
| Scenario estimate | `min(missing_MBID_listens, max(0, target_coverage × total_listens − tagged_listens))`. |

Counts are whole numbers and rates are percentages with one decimal place.
Blank or uncertain values appear as `Unknown` or `Not available`, never as
silently converted zeros. Bulk importers are labeled and can be excluded.
Every result shows its active period and methodology settings.

The **Shortlist** tab is the initial screen because it answers the first
decision: which client should the lead investigate? If no client passes the
filters, show the active filters and an explanatory empty state.

## Shared view rules

- The observation period is shown above every result. It is based on the
  playback timestamp (`listened_at_utc`), not the daily file's submission date.
- Every metric has a plain-language label and a short help description.
- Counts are whole numbers. Coverage and other rates are percentages with one
  decimal place.
- Missing or uncertain client, version, or identifier information is shown as
  `Unknown` or `Not available`; it is not silently treated as zero.
- Bulk importers are marked clearly and can be excluded by the user.
- A missing recording MBID is an observed gap, not proof that the client caused
  the problem. This warning appears near the ranking and scenario results.
- Views show a short methodology note containing the active date range,
  importer setting, minimum-account threshold, ranking weights, and coverage
  target where relevant.

## 1. Outreach shortlist

### Purpose

Give the project lead a ranked shortlist of candidate clients and make the
trade-off between reach and metadata opportunity visible.

### Inputs

- Filtered listen records or a precomputed aggregate table by client.
- Playback-date range.
- Whether bulk importers are included.
- Minimum distinct-account threshold.
- Ranking weights for affected-account reach and missing-MBID listen volume.

### Main table

Display one row per submission client, sorted by the calculated priority score
from highest to lowest. Show these columns:

| Column | Meaning |
|---|---|
| Rank | Position under the current settings. |
| Client | Reporting client name. |
| Priority score | Transparent combined score; show the active weights in help text. |
| Total listens | All observed listens for the client in the selected period. |
| Distinct accounts | Number of observed ListenBrainz accounts using the client. |
| Affected accounts | Accounts with at least one listen missing a recording MBID. |
| Missing-MBID listens | Listens without a recording MBID. |
| Recording-MBID coverage | Share of listens containing a recording MBID. |
| Client type | Regular client, bulk importer, or unknown. |

The table is the primary decision surface. Use compact number formatting, a
sticky header, and enough width for the metric names. Highlight the top three
rows with a subtle accent color, but do not imply that rank is a causal or
guaranteed recommendation.

### Supporting chart

Show a scatter plot below or beside the table:

- x-axis: distinct affected accounts;
- y-axis: missing-MBID listens;
- one point per client;
- point size: total listens;
- color: regular client versus bulk importer;
- tooltip: client name, accounts, missing-MBID listens, and coverage.

Use a log scale only if the values are highly skewed, and label that choice.
Clicking a point or table row selects that client and opens its detail view.
Selection must not expose individual accounts.

## 2. Client detail

### Purpose

Help the lead check whether a selected client's opportunity is broad and
credible enough to justify further outreach.

### Inputs

- One selected client from the shortlist.
- The same active filters and observation period as the shortlist.

### Layout

At the top, show four metric cards:

1. total listens;
2. distinct observed accounts;
3. missing-MBID listens;
4. recording-MBID coverage.

Below the cards, show a 100% stacked bar with `Recording MBID present` and
`Recording MBID missing`. Put the exact counts and denominator in the tooltip
and nearby text so the percentage is not shown without its sample size.

If playback dates cover more than one week, show a weekly line chart with:

- total listens as a light line or area;
- missing-MBID listens as a contrasting line;
- recording-MBID coverage as a separate percentage line or secondary chart.

Do not connect weeks with no observations as if they were measured. Mark gaps
or display them as missing.

If client-version data is available, show a table with client version, listens,
distinct accounts, missing-MBID listens, and recording-MBID coverage. Put
unknown versions last and include a note when version coverage is incomplete.

At the bottom, show an **Assumptions and limitations** panel containing the
active filters, number of observations, missingness notes, and the statement
that the data is observational and not representative of all client users.

## 3. Scenario comparison

### Purpose

Let the lead compare two or more candidates under a possible coverage target
without presenting the result as a guaranteed improvement.

### Controls

- Select two or three clients from the shortlist.
- Set a target recording-MBID coverage, such as 50%, 75%, or 90%.
- Keep the date range, importer rule, and minimum-account threshold visible.

### Charts and table

Show a grouped bar chart for each selected client with:

- current MBID-tagged listens;
- observed missing-MBID listens;
- additional tagged listens in the scenario.

The scenario estimate is:

`max(0, target coverage × total listens − current MBID-tagged listens)`

Cap the estimate at the observed missing-MBID listens and label it
**scenario estimate**, not predicted impact.

Also show a comparison table containing client, affected accounts, missing-MBID
listens, current coverage, target coverage, estimated additional tagged
listens, and the assumptions used. Sort by estimated additional tagged listens
unless the user chooses a different metric.

Use the same client colors across the chart and table. A warning above the
chart should say that the estimate assumes the selected target is attainable
and does not establish that the client can or will make the change.

## 4. Outreach briefing and export

### Purpose

Provide a short aggregate summary that the lead can review before human
outreach.

### Contents

The briefing shows:

- selected client and rank under the current settings;
- observation period and importer treatment;
- total listens, distinct accounts, affected accounts, missing-MBID listens,
  and current coverage;
- selected comparison or scenario results, if any;
- available version evidence;
- ranking weights, coverage target, and calculation definitions;
- data-quality warnings and limitations.

The export is a CSV or Markdown/HTML briefing containing aggregate rows only.
It must not contain usernames, account IDs, raw listens, track-level records,
or listener-level examples. The page should show a confirmation that the
briefing is an evidence summary for human review, not an automated outreach
message.

## Page organization

Use a sidebar for the date range, importer toggle, minimum-account threshold,
ranking weights, and scenario target. Use tabs for:

1. **Shortlist** — ranking table and reach/opportunity scatter plot;
2. **Client detail** — selected-client metrics, coverage, trends, and versions;
3. **Scenario comparison** — candidate comparison and target-coverage estimate;
4. **Briefing** — assumptions, limitations, and aggregate export.

Changing a sidebar setting recomputes all views using the same filtered data.
Selecting a client changes the detail, scenario, and briefing views without
reading or displaying listener-level data.

## Design choices and reasons

- **Aggregate inputs only:** protects listener privacy and keeps rendering fast
  after loading and aggregation are complete.
- **Table plus scatter plot:** the table supports an exact shortlist while the
  chart makes the reach-versus-opportunity trade-off visible.
- **Separate detail and scenario views:** the lead can inspect observed
  evidence before interpreting a hypothetical target as a scenario.
- **Settings shown with every result:** rankings depend on date range, imports,
  thresholds, and weights, so results remain auditable when exported.
- **Aggregate export only:** supports outreach preparation without exposing
  listener-level information.

## Done-when checks

1. On a tiny invented table with two clients, shortlist totals, distinct
   accounts, affected accounts, missing-MBID listens, and coverage match
   independently calculated values.
2. A client with no recording MBIDs shows 0% coverage without a divide-by-zero
   error. No matching clients produces an explanatory empty state.
3. Excluding a bulk importer removes it from both the table and scatter plot,
   while the importer setting remains visible.
4. Clicking a shortlist row updates the detail tab to that client and does not
   display another client's metrics.
5. For 100 total listens, 20 tagged listens, 80 missing listens, and a 75%
   target, the scenario estimate is 55 (`75 - 20`) and never exceeds 80.
6. A missing week is displayed as missing rather than connected by an invented
   trend, and unavailable version data appears as `Unknown`.
7. An exported briefing contains aggregate metrics and settings but no
   `user_id`, `user_name`, track, or raw-listen column.
8. With no selected client, the detail, scenario, and briefing views explain
   what the user must select instead of crashing or showing stale results.
