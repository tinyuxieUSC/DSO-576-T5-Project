# Views — Client Metadata Outreach Prioritizer

The app is for a MetaBrainz project lead deciding which active ListenBrainz
client maintainer to approach first. All views use aggregate data. They must
never display `user_id`, `user_name`, individual listens, or any other
listener-level identifier.

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
