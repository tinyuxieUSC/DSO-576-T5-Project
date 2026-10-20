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

---

# Individual Design Analysis — Module 8

## Part 1. The vision (handout 8.3)

The following is the team's vision from `00-vision.md`.

> # 00 Vision — Client Metadata Outreach Prioritizer
>
> ## User and decision
>
> A MetaBrainz Foundation project lead preparing a quarterly outreach pilot needs to decide **which active ListenBrainz client maintainer to contact first** about improving submission of MusicBrainz recording identifiers (MBIDs). The tool supports a human outreach decision; it does not contact maintainers automatically.
>
> ## Why this is useful
>
> A recording MBID identifies a specific recording more reliably than artist and track text alone. Today, a project lead would have to inspect listening-data exports, group records by the software that submitted them, distinguish active listening clients from historical importers, and manually compare results. Ranking clients only by listen volume can overvalue a few heavy users or bulk imports; ranking only by missing-ID percentage can overvalue tiny clients.
>
> The **Client Metadata Outreach Prioritizer** makes the trade-offs visible in one Streamlit app: a ranked shortlist, a closer look at a selected client, and a comparison of potential improvement scenarios. It helps the lead select a promising pilot partner based on evidence rather than a single raw count.
>
> ## What the user cares about
>
> - **Reach:** how many distinct accounts could benefit, not just how many listens a client submits.
> - **Opportunity:** how many listens lack a recording MBID, alongside the client's current MBID coverage.
> - **Relevance:** separating regular submission clients from bulk importers, and showing the observation period.
> - **Transparency:** seeing how rankings and estimates were calculated, including uncertain or missing evidence.
> - **Practical action:** selecting a small number of clients for further research without exposing individual user identities.
>
> ## Concrete use cases
>
> 1. **Build a pilot shortlist.** The lead selects a playback-date range, excludes bulk importers, and sets a minimum distinct-account count. The tool shows a ranked table with each client's total listens, accounts, affected accounts, missing-MBID listens, and current coverage. The lead chooses two or three maintainers to investigate.
>
> 2. **Check a candidate's data quality.** The lead selects a client from the shortlist. The tool shows its metrics, available client-version breakdown, and the assumptions behind its ranking. The lead decides whether the missing-ID opportunity is broad enough to justify contacting its maintainer.
>
> 3. **Compare competing priorities.** The lead adjusts the emphasis on affected-account reach versus missing-MBID volume and compares two candidates. The tool shows how rankings change and estimates additional MBID-tagged listens under a user-selected coverage target. The lead chooses which pilot is more attractive, understanding that the estimate is a scenario rather than a guaranteed result.
>
> 4. **Prepare for outreach.** After choosing a candidate, the lead reviews and exports a short aggregate-data briefing containing the client's metrics, selected settings, and assumptions. The lead uses it for a human review and decides whether to begin a pilot conversation.
>
> ## Boundaries
>
> The tool analyzes observed ListenBrainz data, not the full population of client users. A missing MBID does not prove that the submitting client caused the problem. Rankings and scenario estimates are **screening aids**, not causal findings, guarantees of improvement, or automated outreach decisions. Identifiable listener-level data is never shown in the interface or exports.

## Part 2. My design analysis (handout 8.3)

These answers address the four design questions in the Module 8.3 analysis template and the open questions for this project, with emphasis on my assigned `05-views.md` responsibility: charts, tables, visual design, and interactions.

### 2a. Clear pieces

The design has five pieces with separate responsibilities and explicit inputs/outputs:

- **Data rules** receives raw field values and policy; returns canonical cleaned values and statuses.
- **Loader/preparation** receives configuration and source paths or a prepared-data handle plus filters; it reads the listening data and returns a prepared handle, aggregate DataFrames, and data status.
- **Filters/scoring** receives internal grouped batches or aggregate client metrics and settings; returns filtered aggregates, ranks, sensitivity results, and scenarios without file or Streamlit access.
- **Views** receives aggregate tables plus settings/status; renders the shortlist, client detail, scenario comparison, and briefing, returning only selected client names to shared state.
- **Setup/app** receives TOML configuration and user choices; validates settings, wires components together, and owns shared navigation/selection.

The clear-pieces option fits because each job can be specified and checked at its boundary. For my views piece specifically, receiving aggregate inputs rather than raw listening rows means chart and table work does not also take on data cleaning, counting, or file access.

### 2b. Simple connections

Only the loader/preparation component reads the source listening files and prepared Parquet. Views must never open CSV, Parquet, or raw JSON, calculate listener-level metrics, or receive account identifiers/HMAC keys. The filters component may handle internal grouped batches for aggregation but has no file or Streamlit access. Views receive aggregate client/version/week results, settings, and status; a chart or row selection returns only a client name to shared dashboard state. This keeps the connections simple and prevents the display from depending on storage or another view's internals.

### 2c. Local changes

On screen, the user can change inclusive playback dates, importer exclusion, minimum accounts, ranking emphasis, scenario coverage target, and selected/comparison clients. The matching controls belong in setup/shared state; ranking and scenario calculations belong in filters; chart, table, labels, and interaction behavior belong in views.

Likely future changes include a new visual treatment, an additional view, a revised metric definition, or a changed default. A visual change should be made in the views contract (and its relevant acceptance check), while a metric definition should have one authoritative home in data rules and be passed through aggregates. Defaults and classifications belong in configuration. This follows local-change design: changing a chart should not require changing data preparation, and changing a definition should not produce inconsistent calculations across screens.

### 2d. Real-world operation

The combined prompt identifies the local full JSONL input as 3,966,393,313 bytes and the sample as 21,276 events (21,278 physical lines including its header and quoted multiline record). These are the specified input facts; the full-file totals must be recomputed during preparation rather than inferred from the separate overview dataset.

Preparation reads raw data in bounded chunks, groups cleaned events, and writes compressed monthly-partitioned Parquet while retaining exact playback dates. At startup, the app loads validated configuration and the completed-cache manifest/status, then queries aggregates for the initial shortlist. On filter changes or navigation, it queries the prepared data with date and importer filters and renders aggregates; weight and target changes reuse base aggregates. Selecting a client triggers the corresponding aggregate detail query. It must not reread raw inputs or expose account-level rows on a dashboard rerun.

The query memory budget is defined as total process RSS, with a default of 1,024 MiB; buffers and exact account-key sets are bounded, with spill-to-disk when needed. For the views piece, only the selected aggregate tables, their chart/table representations, settings, and status need to be in memory—not the full listening history or account identities. The application retains a completed prepared cache and aggregate query results keyed by data fingerprint/mode/filters; it does not retain raw event records in Streamlit state. This prepared-once/query-aggregates approach fits the large input and interactive use.

### 2e. Open questions

- The prompt defines scenario additions as hypothetical and requires an attainability/causality warning. The remaining visual question is the exact encoding that best distinguishes these hypothetical additions from observed counts while fitting the dashboard; the proposed improvement specifies a separate legend and a visually distinct outline/pattern. Confirm the encoding in a review of the rendered chart, without changing the distinction itself.
- The vision refers to an “active” client maintainer, but observed submission data cannot establish current maintainer activity. The interface should present candidates as evidence for further research, not claim current activity; confirm with the team that this limitation is explicit in the shortlist and briefing.
- Verify the selected actual dataset and its available dates before presenting a full-mode result. The prompt correctly requires recomputing full counts and prohibits treating the sample or another dump's totals as the selected input's results.

## Part 3. My improvement to the draft prompt (handout 8.8)

**What I improved, in one sentence:** In Section 7, I specified that the scenario-comparison chart visually separates hypothetical additions from observed listen counts and added an acceptance check for that distinction.

### 3a. Before

The following is the original Scenario comparison row and the adjacent acceptance check from `one-shot-prompt.md` before my change:

````text
| **Scenario comparison** | Select two or three clients from the complete eligible population; grouped bars for current valid-ID listens, unusable-ID listens, and scenario additions; table with accounts, current/target coverage, additions, and assumptions. Sort additions descending, then client. Stable client colors and a visible attainability/causality warning. |

Acceptance check: if alpha has accounts A and B, and beta has accounts B and C, display two accounts for each client without reporting four unique accounts overall.
````

### 3b. After

The following is the revised Scenario comparison row and both adjacent acceptance checks in `one-shot-prompt.md`:

````text
| **Scenario comparison** | Select two or three clients from the complete eligible population. In the grouped bar chart, show current valid-ID listens and unusable-ID listens as observed values, and show additional tagged listens as a visually distinct hypothetical scenario estimate (for example, with an outline or pattern and a separate legend entry). Do not stack or otherwise present scenario additions as observed listens. Include a table with accounts, current/target coverage, additions, and assumptions. Sort additions descending, then client. Use stable client colors and show the attainability/causality warning. |

Acceptance check: if alpha has accounts A and B, and beta has accounts B and C, display two accounts for each client without reporting four unique accounts overall.

Acceptance check: in the scenario comparison chart, observed listen counts are visually distinguishable from hypothetical additions; the scenario estimate is not presented as observed data and never exceeds unusable-ID listens.
````

### 3c. Why it is better

This improves **one-shot-prompt-specs criterion 8, Complete**: before the change, an agent could choose a grouped-bar encoding that makes scenario additions look like measured listening data, leaving an important interpretation choice to guesswork. The new contract explicitly identifies which bars are observed and which are hypothetical, prohibits stacking them as if they were observed, and gives a checkable condition that the estimate stays within the observed unusable-ID opportunity. It also supports **criterion 3, Clear**, by giving the chart one unambiguous interpretation.

The Section 8.4 design practice is to give a piece a clear responsibility/contract and make it independently checkable. This change stays within the views piece: it defines the scenario chart's display behavior and adds a targeted acceptance check, without changing data rules or scenario calculations. This is significant because an incorrect visual implication could lead a project lead to mistake a what-if estimate for an observed result. It is distinct from the teammate's account-reach improvement: it does not alter account measures, reach definitions, or the shortlist; it concerns only the visual distinction between observed counts and hypothetical scenario additions.
