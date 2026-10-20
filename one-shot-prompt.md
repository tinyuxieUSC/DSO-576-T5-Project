# Build the Client Metadata Outreach Prioritizer

Build and validate a local Streamlit application from this specification and the dataset repository `USC-DSO-576-PS/dataset_listenbrainz`. This file is self-contained: do not require the team's separate component files or Module 5 prototype. Implement the build below; leave cosmetic styling to your judgment.

## 1. User, decision, and design

A MetaBrainz Foundation project lead preparing a quarterly outreach pilot needs to decide which observed ListenBrainz submission-client maintainer to investigate and contact first about recording-MBID coverage. Today this requires separate queries and manual comparison. The tool puts account reach, missing-identifier volume, coverage, and assumptions together so a few heavy users or bulk imports do not decide the ranking alone.

The lead can (1) select playback dates, exclude importers, and set minimum account reach to obtain a shortlist; (2) select a client to inspect versions and coverage; (3) change ranking emphasis and compare two or three clients under a hypothetical coverage target; and (4) download an aggregate briefing for human review. These are screening aids, not causal findings, maintainer-feasibility estimates, forecasts, or automated outreach. Observed submissions do not represent all users of a client; observed activity does not establish that a maintainer is currently active.

Design principles:

- **Define measures once:** data rules own definitions; preparation and queries implement them, preventing contradictory screens.
- **Prepare once, query prepared groups:** pandas handles bounded batches and compressed Parquet stores the result. Never load the entire raw listening file into memory or reprocess it during a dashboard interaction.
- **Keep identities internal:** stable account keys support exact counts, but only client/version/week aggregates reach views or exports. Hashes remain identifiers, not public output.
- **Separate policy from display:** defaults and classification are configuration; scoring is pure pandas; views only render results. Each piece must be independently checkable.

| Piece | Responsibility | Receives → returns |
|---|---|---|
| `outreach/data_rules.py` | Field mappings, normalization, validation, metric definitions | Raw field values + policy → cleaned values/statuses; no file access |
| `outreach/loader.py` and `outreach/prepare.py` | The only listening-data readers/writers; preparation, exact aggregate queries, provenance/cache | Config + source paths or prepared handle + data filters → prepared handle, aggregate DataFrames, status |
| `outreach/filters.py` | Pure batch selection/aggregation helpers, eligibility, scoring, sensitivity, scenarios | Internal grouped batches or client aggregates + settings → client aggregates, ranks, scenarios; no file or Streamlit access |
| `outreach/views.py` | Shortlist, detail, comparison, briefing | Aggregate tables + settings/status → rendered views and selected client names |
| `outreach/setup.py` and `app.py` | Config validation, controls, shared state, startup/wiring | TOML + user choices → validated settings and calls between components |

The loader may call pure filtering helpers on internal grouped batches. A batch-selection helper can return internal rows only to the loader; the public boundary to views returns aggregates exclusively. Preparation implements `data_rules.py`; there is no second independent cleaning pipeline.

## 2. Source access and evidence

Use a configurable dataset root, normally the sibling folder `../dataset_listenbrainz`. Treat repository reference material and existing input files as read-only. Keep generated data in the application directory and out of Git.

| Mode | Input |
|---|---|
| `sample` | `<dataset_root>/sample/listens_20260904.csv`, 21,276 sampled events; use a real CSV parser with selected string columns and explicit blank handling. Its 21,278 physical lines include a header and one quoted multiline record. |
| `full` | An explicit configured list of extracted `.listens` files. Initial known path relative to dataset root: `data/listenbrainz-listens-dump-2657-20260910-000003-incremental/listens/2026/9.listens` |

The local full input is 3,966,393,313 bytes, UTF-8 nested JSON with one event per line. Its `SCHEMA_SEQUENCE` is `1`; `START_TIMESTAMP` is `2026-09-09 00:00:02.717236+00:00` and `END_TIMESTAMP` is `2026-09-10 00:00:03.308037+00:00`. These describe submission collection, not when each event was played. A single file contains historical playback and does not provide complete playback history for any selected period.

Inspection of its first 1,000 events found 2 syntactically valid submitted recording MBIDs, 0 absent client names, and 990 absent versions. This sequential subset is structural evidence only. The overview's 4,411,662 events and 3.22% MBID coverage concern another file; do not reuse them as this input's totals. Recompute full counts during preparation.

No reference-table join or auxiliary service is required for this product. The June 2025 metadata snapshot is not another listening dataset. Identifier coverage is distinct from matching to that reference sample.

For a new machine, document access to the dataset repository, its README, `data_overview_listenbrainz.md`, and `sample/README.md`. An existing extracted input is sufficient. For missing full inputs, follow the overview's download links and publisher checksums; read its supplied download/unpack scripts as references, but implement a destination-configurable equivalent under application-owned `data/raw/` if needed. Do not run helpers that write into a read-only dataset checkout. Verify checksums, extract safely, and require explicit input selection; downloads/unpacking never occur implicitly on a Streamlit rerun. If access/download fails, explain the path/browser route; do not substitute a sample silently. Reproduce the sample path first when full data is unavailable.

## 3. Canonical data rules

| Canonical value | Raw JSON field | Flattened CSV field |
|---|---|---|
| Account identity | `user_id` | `user_id` |
| UTC playback date | `timestamp` in Unix seconds | `timestamp`; derive dates using the same conversion |
| Client | `track_metadata.additional_info.submission_client` | `ai_submission_client` |
| Version | `track_metadata.additional_info.submission_client_version` | `ai_submission_client_version` |
| Submitted recording MBID | `track_metadata.additional_info.recording_mbid` | `ai_recording_mbid` |

Implement separate raw-JSON and CSV adapters into the same canonical rules. Extract only required fields. Ignore unrelated optional keys and never retain usernames, track names, or full raw records in caches/logs.

- Parse timestamps as UTC; reject absent, nonnumeric, or unrepresentable values and count each reason. Preserve valid historical dates. Flag events later than their full dump's end but do not clip timestamps. Sample data has no corresponding current full-dump interval; do not borrow the September 10 interval for it.
- Accept positive integer account IDs (or strings expressing them), excluding booleans. Encode each using HMAC-SHA256 with an application-local random secret, stable across dates and source files. Preserve the secret outside Git; changing it requires rebuilding the complete cache. Invalid/missing accounts become null, remain in listen counts, and are excluded from distinct counts.
- Trim client names, use case-folded canonical identity keys, and apply only explicit aliases. Null/blank/non-string clients become `NOT_REPORTED`. Do not infer client identity from player/service fields. Preserve raw-label counts in the preparation report to audit normalization.
- Versions are trimmed free text; never numeric. Missing/blank/non-string values become `NOT_REPORTED`.
- For MBIDs, null/absent/blank is `missing`; a trimmed string matching canonical hexadecimal UUID shape `8-4-4-4-12` is `valid` after lowercasing; all other populated values are `invalid`. This checks syntax, not existence in MusicBrainz. Do not substitute recording MSIDs, release IDs, or `lastfm_*` IDs.
- **Opportunity includes both missing and invalid IDs.** Preserve their separate counts. UI labels say “without a usable recording MBID” and explain this definition.
- `client_type` is `regular`, `importer`, or `unknown`, based only on the configured evidence-backed exact mapping. Unlisted clients remain `unknown`, not implicitly regular. `NOT_REPORTED` clients are visible in diagnostics but never outreach-ranked. Named clients with unknown type can be ranked and are visibly labeled as unverified classification.
- Use the configured exact importer mapping for classification. An unlisted case-folded client name containing `import`, `archive`, or `takeout` generates a warning-only review suggestion; it remains unknown. Exclusion removes classified importer rows only, not every row submitted by the same account.
- Reject malformed JSON or non-object structural blocks with reason, filename, and line number only. Optional absent `additional_info` is an empty block, not a rejected event. Stop clearly on unsupported full-input schema sequence or zero accepted events.
- Skip repeated input files by content hash. Across distinct files, warn when source collection intervals intersect (`start_a < end_b` and `start_b < end_a`) or an interval is unavailable; retain records by default. Overlap is a risk flag, not proof of duplicate events. Only an explicit documented policy backed by a stable event identifier may remove events. Never delete merely matching account/track/timestamp rows. The default single-file build does not invent an event identity.

## 4. Preparation, storage, and exact queries

Use Python JSON reading, pandas, and PyArrow. Start with `chunk_size = 10000` raw lines. Group each cleaned batch by `(play_date, client, client_version, account_key)`, retaining null accounts. Store Zstandard-compressed Parquet under `data/prepared/<fingerprint>/play_month=YYYY-MM/`. **The month is only a physical storage partition: retain the exact UTC `play_date` in every grouped row.** Do not create a separate file for every playback date in every input chunk.

Coalesce temporary fragments into larger month files using bounded buffers. Within each output fragment, combine equal group keys by summing their counts and sort by `play_date, client`; null accounts remain a group. Target 32–128 MiB compressed files when a month has sufficient data, with 10,000-row Parquet row groups. Small months may use one smaller file, and large months may span several files. Bound the total buffer memory across months and compact incrementally; never load the full history just to compact it. This changes storage layout, not daily filter precision, client metrics, or eligibility rules.

**Evidence for this layout:** An AI-assisted feasibility experiment selected every 40th physical line from the September 10 incremental input, giving 169,524 events. The date-per-chunk layout produced 45,440 files and an all-date query took 51.983 seconds. Month compaction produced 260 files containing 78,645 grouped rows; three query-only runs took 0.397, 0.395, and 0.400 seconds. Every client's listen, valid/unusable-ID, distinct-account, and affected-account counts agreed with an independent raw-subset count. Environment: macOS ARM64, Python 3.14.7, pandas 3.0.6, PyArrow 25.0.1. These are systematic-subset measurements, not full-size or cold-disk guarantees; OS caches were not flushed. Experimental compaction loaded only the bounded subset and peaked near 2.07 GiB, so it does not validate bounded full-size preparation. Production must implement the bounded compaction above and measure its memory separately.

| Prepared column | Type/meaning |
|---|---|
| `play_date` | UTC calendar date |
| `client`, `client_version` | Canonical text identities |
| `account_key` | Nullable internal HMAC text |
| `client_type` | Configured category |
| `listens` | Positive integer count |
| `valid_mbid_listens` | Count with valid UUID syntax |
| `missing_mbid_listens` | Count with absent/blank ID only |
| `invalid_mbid_listens` | Count with populated invalid ID |

Each fragment has unique group keys; keys may recur across fragments. The three MBID counts must sum to `listens`. Queries sum counts across fragments and deduplicate account keys across the entire selected period. Repeated keys across fragments are not duplicate source events.

Prepare in a temporary directory and publish a manifest atomically after success. Record input paths/checksums/schema/mode, source collection intervals, accepted/rejected/duplicate-file counts, quality distributions, actual playback bounds, normalization/classification rules and secret-version fingerprints, timings, and raw/prepared sizes. Never record the secret itself. An interrupted run preserves the previous completed cache.

For queries, use PyArrow to prune `play_month` partitions intersecting the selected range, then apply the exact inclusive `play_date` predicate and project only needed columns before streaming record batches to pandas. Use both the month and day predicates, including for a range crossing a month boundary. Keep only bounded batches, numeric accumulators, and exact per-client account-key sets in memory. Do not concatenate all selected fragments or cache the complete account-level table in Streamlit. For versions/weeks, key internal distinct sets by those groups as well. Never sum per-day or per-version distinct-account counts. Repeated group keys across different files must still be combined; file compaction must not be treated as event deduplication.

**Exact counts within the memory budget:** Interpret `query_memory_budget_mb` as a limit on total query-process RSS in MiB (1,048,576 bytes), including interpreter/libraries, scanner metadata, buffers, and distinct-key sets. Use psutil to measure live RSS and include it in `requirements.txt` as a loader dependency. Measure the baseline first; reject an infeasible budget below the baseline plus space for a batch. Reserve headroom for the next batch. Measure preparation memory separately and use the bounded compaction already specified.

When distinct-key sets approach the limit, spill internal `(group, account_key, affected)` pairs into temporary Parquet buckets determined by the account hash prefix. The same account always enters the same bucket across fragments and dates. Use pandas to deduplicate one bucket at a time, taking logical OR of `affected`, then add its exact distinct/affected counts to the client totals. Version/week group keys must remain part of the deduplication key. Drop null account keys from account counts only. Split an oversized bucket using a longer prefix; check temporary disk availability and remove temporary spill files after success or failure. Do not approximate counts, truncate the date range, or suppress clients to fit memory. Test the spill route with a deliberately small internal key-set allowance while keeping the process budget above the interpreter baseline.

Apply playback dates and importer rules before aggregation; apply minimum-account eligibility to whole-client results. Version/weekly detail inherits the parent's eligibility, not a separate threshold per version/week. Source diagnostics remain available even when no client qualifies.

Return these exact client columns:

| Column | Definition |
|---|---|
| `client`, `client_type` | Canonical identity and classification |
| `total_listens` | Sum of retained `listens` |
| `with_recording_mbid` | Sum of `valid_mbid_listens` |
| `absent_recording_mbid` | Sum of `missing_mbid_listens` |
| `invalid_recording_mbid` | Sum of `invalid_mbid_listens` |
| `missing_recording_mbid` | Absent + invalid; outreach opportunity |
| `coverage` | `with_recording_mbid / total_listens`, fraction 0–1 |
| `distinct_accounts` | Exact distinct non-null account keys |
| `affected_accounts` | Exact distinct non-null keys with an absent or invalid ID |
| `unknown_account_listens` | Listen count with null account key |
| `unknown_version_listens` | Listen count with `NOT_REPORTED` version |
| `first_play_date`, `last_play_date` | Observed filtered bounds |

Expose these public contracts, with dataclasses/type hints and correctly typed empty tables:

```python
prepare_data(config: AppConfig) -> PreparedDataset
get_client_metrics(data: PreparedDataset, query: DataFilters) -> pd.DataFrame
get_version_metrics(data: PreparedDataset, query: DataFilters,
                    client: str) -> pd.DataFrame
get_weekly_metrics(data: PreparedDataset, query: DataFilters,
                   client: str) -> pd.DataFrame
get_data_status(data: PreparedDataset) -> DataStatus
rank_clients(metrics: pd.DataFrame, reach_weight: float) -> pd.DataFrame
rank_sensitivity(metrics: pd.DataFrame, weights: list[float]) -> pd.DataFrame
estimate_scenarios(metrics: pd.DataFrame, clients: list[str],
                   target: float) -> pd.DataFrame
```

`PreparedDataset` carries completed cache paths/fingerprint/mode/provenance. `DataStatus` exposes aggregate diagnostics, source intervals, available dates, and warnings. `DataFilters` contains inclusive start/end dates, importer exclusion, and minimum accounts. Application settings additionally contain weight, target, selected detail client, and comparison clients; setup passes only `DataFilters` to base queries. Client selections must not change the scoring population.

Version results add `client_version` to the client measures. Weekly results add `week_start`, Monday 00:00 UTC; respect partial selected weeks. Query selected dates once, then bin internally. Reindex absent weeks as unavailable, not measured zero coverage. Public query returns never include `account_key`, raw account IDs, hashes, usernames, or event-level rows.

## 5. Eligibility, ranking, and scenario calculations

Use the configured account floor and `max(user_minimum, floor)`. Rank named clients meeting that threshold, with importer exclusion already applied. Rank all eligible clients before taking a top ten or selecting comparison candidates. Keep unknown-client diagnostic totals separately.

Use the log-normalized formula supplied in the filters component, not the older prototype's percentile formula:

```text
norm(x) = log1p(x) / log1p(max(x over all rankable clients))
          or 0 when that maximum is 0
score = w * norm(affected_accounts)
      + (1 - w) * norm(missing_recording_mbid)
```

The score is 0–1 and is not a probability. Sort by score descending, missing-recording-MBID listens descending, then canonical client ascending. Assign sequential ranks starting at 1. Sensitivity recomputes scores/ranks over the same eligible population for weights `[0.0, 0.5, 1.0]` and the current weight, removing duplicate weights.

For target `t` in 0–1:

```text
raw_additional = min(missing_recording_mbid,
                     max(0, t * total_listens - with_recording_mbid))
additional_tagged_listens = round(raw_additional)
```

Use Python's round-to-nearest/ties-to-even rule and return an integer. This is an approximate scenario count, not a promise to attain a precise target after rounding. A target at/below current coverage yields zero. Use the same selected listens, accounts, and dates; assumptions and target must accompany the result.

## 6. Configuration, startup, and interaction

Create `config.toml`, `outreach/__init__.py`, the modules above, `app.py`, `requirements.txt`, tests, and a README. Use Python 3.11+; dependencies are pandas, PyArrow, Streamlit, Altair, and pytest for tests. Record tested dependency versions after building. No database server, SQL engine, account credentials, or AI API is required.

Provide this editable starting configuration; paths resolve relative to the config file, with `dataset_root` used for dataset-relative input paths:

```toml
[paths]
dataset_root = "../dataset_listenbrainz"
prepared_root = "data/prepared"
secret_file = ".local/account-key.secret"
sample_input = "sample/listens_20260904.csv"
full_inputs = ["data/listenbrainz-listens-dump-2657-20260910-000003-incremental/listens/2026/9.listens"]

[preparation]
mode = "sample"
chunk_size = 10000
rules_version = "1"

[defaults]
initial_tab = "Shortlist"
date_range = "observed_bounds"
exclude_importers = true
minimum_accounts = 100
minimum_accounts_floor = 5
reach_weight = 0.5
target_coverage = 0.75
shortlist_size = 10
query_memory_budget_mb = 1024

[classification]
importers = ["ListenBrainz lastfm importer v2", "ListenBrainz Archive Importer", "Takeout Importer Script", "Node-RED Plex Import", "https://github.com/BlakeAlvarez/YTMusic-ListenBrainz-Importer"]
regular_clients = ["navidrome", "Pano Scrobbler", "Web Scrobbler", "ListenBrainz Android", "Roon"]

[aliases]
```

Canonicalize mapping keys with the same trim/case-fold rules. Seed classifications above are supported by the dataset overview's client table and sample labels; record that evidence in generated config comments/README. Other labels, including `ArchiveTune`, remain unknown pending review. The editable account floor reduces tiny-count displays; it is not an anonymity guarantee. An empty alias map is intentional.

Before startup, validate the configuration and report specific, actionable errors:

- Check that the selected dataset mode matches an existing completed cache. If the cache is missing, identify the mode and provide the preparation command. Never switch modes automatically.
- Validate date bounds and resolve `observed_bounds` from accepted playback dates. Explain invalid date ranges and disclose historical or future-date warnings.
- Require minimum accounts to be a nonnegative integer, and the account floor, chunk size, and memory budget to be positive integers.
- Require reach weight and target coverage to be between 0 and 1. Ensure importer and regular-client classification sets do not overlap.
- For each validation error, identify the setting name, invalid value, expected range, and suggested correction. Never silently repair invalid settings.
- Start with no client selected. If valid filters return no eligible clients, show a clear empty-state message rather than a startup error.

Supply and verify these commands from the application directory after generating the files:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m outreach.prepare --config config.toml --mode sample
python -m pytest
python -m streamlit run app.py -- --config config.toml
```

For full mode, set `full_inputs` to real extracted paths, prepare using `--mode full`, then start with `--config config.toml --mode full` after Streamlit's `--` separator. CLI mode overrides TOML mode for that invocation and selects a separate cache; never fall back between modes. Include an explicit `--rebuild` preparation option. Put `.venv/`, `.local/`, raw/prepared data, temporary files, and diagnostic logs in `.gitignore`.

Setup renders sidebar controls for inclusive UTC dates, importer exclusion, minimum accounts (bounded below by the configured floor), reach weight 0–100%, and target coverage 0–100%. Convert percentages to fractions once. Show complementary volume weight. Invalid date ranges show a corrective message; valid empty selections show an empty state.

Cache only aggregate query results keyed by the completed preparation fingerprint, mode, and all data-filter values. Preparation fingerprint includes source hashes and rule/alias/classification/secret versions; use path/size/mtime checks to avoid hashing raw gigabytes on each startup, with explicit verification/rebuild available. Weight, target, selection, and navigation changes reuse base aggregates. Detail queries add selected client and version/week grouping to cache keys. Clear stale selections when eligibility changes.

## 7. Screens and exports

Always show sample/full mode, selected playback dates, source submission interval(s) when known, sample sizes, active methodology, and observational limitations. Counts are whole numbers; coverage is displayed as percent with one decimal, without changing its stored fraction.

| Tab | Required output |
|---|---|
| **Shortlist — first screen** | Decision description; top ten eligible clients with rank, score, client/type, total listens, distinct/affected accounts, missing usable IDs, and coverage. Highlight top three subtly. Scatter: affected accounts on x, missing usable IDs on y, size by total listens, color includes all three client types. Show exact counts in tooltips. Optional log axes must handle zeros explicitly. Row/point selection opens detail. |
| **Client detail** | Selected-client cards; valid vs unusable ID stacked coverage bar with denominators and invalid-ID explanation; version table including `NOT_REPORTED` last and known-version share; weekly totals/missing/coverage when selected dates span more than seven days, with missing weeks unconnected and partial weeks labeled. Show assumptions and rank-sensitivity table. |
| **Scenario comparison** | Select two or three clients from the complete eligible population. In the grouped bar chart, show current valid-ID listens and unusable-ID listens as observed values, and show additional tagged listens as a visually distinct hypothetical scenario estimate (for example, with an outline or pattern and a separate legend entry). Do not stack or otherwise present scenario additions as observed listens. Include a table with accounts, current/target coverage, additions, and assumptions. Sort additions descending, then client. Use stable client colors and show the attainability/causality warning. |
| **Briefing** | Selected client, rank/score, metrics, dates, source/mode, filters, weights, target/scenario if chosen, version evidence, formulas, and quality warnings. Download aggregate CSV and a concise Markdown briefing; include metadata/settings in the CSV using repeated metadata columns. No automated contact action. |

Show distinct_accounts and affected_accounts separately for each client. Do not sum either measure across clients or display the sum as combined unique account reach in the comparison screen or exports. Include this explanation in both: “An account may use more than one client, so account counts across clients are not additive.”

Acceptance check: if alpha has accounts A and B, and beta has accounts B and C, display two accounts for each client without reporting four unique accounts overall.

Acceptance check: in the scenario comparison chart, observed listen counts are visually distinguishable from hypothetical additions; the scenario estimate is not presented as observed data and never exceeds unusable-ID listens.

No selection shows instructions, not stale metrics. Fewer than two comparison clients shows a selection prompt. Shortlist scatter and comparison selector may include all eligible clients even when the initial table shows ten; label the difference. Offer a full eligible-summary CSV through the briefing/export area. Export only whitelisted client/version/week measures and settings: account counts such as `affected_accounts` are allowed; identifiers and hashes are forbidden.

## 8. Build order and acceptance checks

Build in order: data rules/adapters → preparation/report → streamed aggregate queries → scoring/scenarios → configuration/startup → views/export. Run relevant checks at each boundary. Do not claim measured performance or full-data results before running them.

| Build boundary | Gate before moving to the next stage |
|---|---|
| Data rules/adapters | Equivalent raw/CSV events produce the same canonical values; malformed and edge-case inputs follow the expected acceptance/rejection rules (check 1). |
| Preparation/report | Accepted, rejected, and duplicate-file counts reconcile with the physical inputs (check 4). |
| Streamed aggregate queries | The January fixture returns the expected alpha/beta totals and exact distinct-account counts; chunk-size and cross-fragment checks pass (check 2). |
| Scoring/scenarios | Fixture rankings, sensitivity order, and target additions match the expected results above. |
| Configuration/startup | Invalid settings and missing or mismatched caches produce actionable errors without silently switching modes (check 7). |
| Views/export | Fixture values, selection/empty states, and the export whitelist are verified (check 6). |

Use this internal grouped fixture; keys below stand for test HMAC values. All unusable-ID counts in this fixture are absent IDs; invalid counts are zero. Set the test account floor to 1.

| Account | Client | Version | UTC play date | Listens | Unusable IDs | Type |
|---|---|---|---|---:|---:|---|
| a1 | alpha | 1.0 | 2026-01-01 | 10 | 10 | regular |
| a1 | alpha | 1.0 | 2026-01-02 | 5 | 5 | regular |
| a2 | alpha | 1.1 | 2026-01-02 | 10 | 0 | regular |
| a3 | alpha | 1.1 | 2026-01-03 | 5 | 5 | regular |
| a10 | alpha | 1.1 | 2026-01-03 | 1 | 1 | regular |
| a4 | beta | 2.0 | 2026-01-01 | 100 | 100 | regular |
| a5 | beta | 2.0 | 2026-01-02 | 40 | 20 | regular |
| a6 | beta | 2.0 | 2026-02-01 | 10 | 10 | regular |
| a7 | imp | 1 | 2026-01-01 | 1000 | 1000 | importer |
| a8 | imp | 1 | 2026-01-02 | 1000 | 1000 | importer |
| a9 | solo | 1 | 2026-01-01 | 500 | 500 | regular |

For January 1–31 inclusive, exclude importers, minimum accounts 2, weight 0.5:

- alpha: 31 listens, 10 valid IDs, 21 unusable IDs, 4 accounts (a1 once), 3 affected accounts, coverage `10/31`.
- beta: 140 listens, 20 valid IDs, 120 unusable IDs, 2 accounts, 2 affected accounts, coverage `20/140`.
- Rank beta first (score approximately `0.896241`), alpha second (`0.822266`). Weights 0, 0.5, 1 give beta, beta, alpha first.
- alpha versions: 1.1 has 16 listens, 6 unusable IDs, 3 accounts, coverage `0.625`; 1.0 has 15 listens, 15 unusable IDs, 1 account, coverage `0`.
- At target 0.8, additions are alpha 15 and beta 92; beta at target 0.1 gives 0. The separate 100-listen/20-valid/75%-target example gives 55.
- Including importers adds imp: 2,000 listens, 2 accounts, 2 affected, zero coverage. solo remains below threshold. Extending through February gives beta 150 listens, 130 unusable IDs, 3 accounts.

Also verify:

1. Raw adapters agree on equivalent events. Test UTF-8, absent optional blocks, malformed JSON/timestamps, blank/invalid UUIDs, null accounts, and unknown clients/versions; retain unusable IDs and null-account listens.
2. Chunk sizes 1 and 10, and splitting the same account across fragments/dates/versions, yield identical exact aggregates. Assert `total = valid + absent + invalid`, `affected_accounts <= distinct_accounts`, and version listen totals equal client totals. Do not require version distinct-account totals to sum.
3. Include invalid IDs in opportunity while reporting them separately; unknown accounts add listens but no distinct account. Unknown clients remain in diagnostics but are unranked; named unknown-type clients are labeled rather than falsely classified.
4. Reconcile physical lines for JSONL, including rejected blank lines; reconcile parsed event records for CSV, excluding its header, and report physical lines separately. Preserve quoted newlines: the supplied sample must yield 21,276 events from 21,278 physical lines including its header. Stop on unrecoverable CSV syntax errors rather than guessing record boundaries. Account separately for duplicate-file skips. Compare an independent raw-subset count with preparation/query results for the identical subset; isolate subset caches from sample/full caches. Reproduce the first-1,000-event structural observations before citing them as confirmed.
5. Validate date endpoints, alias mapping, exact importer exclusion, input overlap warnings, partial/missing weeks, zero/all-valid coverage, empty results, rank ties, all-zero score maxima, score bounds, target bounds, and ties-to-even scenario rounding.
6. Screens agree with fixture values, selection updates the correct client, no selection/empty filters do not crash, and exports contain settings and formulas but no identifiers. Test a whitelist; do not reject legitimate aggregate columns merely because their names contain `account`.
7. Input/rule changes invalidate preparation; interrupted preparation leaves the prior cache intact; reruns/weights/targets do not read raw inputs. Missing files, unsupported schema, denied paths, and invalid settings produce actionable errors and never silent sample fallback.
8. Verify the storage-layout change by preparing the same fixed input subset with date-per-chunk and compacted-month layouts. Require exact equality of client totals, valid/absent/invalid-ID counts, distinct/affected accounts, version results, and weekly results. Test a single selected day and January 31–February 1 inclusive so physical month partitions cannot widen the date filter. Record preparation/compaction time, peak memory separately for preparation and querying, Parquet bytes/file count, and first/repeated aggregate-query times on the same laptop and input. Label OS-cache conditions and input size; do not extrapolate subset timings to full data. Then measure the full prepared input with the broadest range and importer inclusion. Aim for a cached interaction below one second, labeling this as a target. Enforce the configured memory budget; if resources are insufficient, report that explicitly rather than approximate counts or change dates. Do not change engines or coarsen dates silently.
9. A new reader can follow the README to prepare sample data, run tests, and open the initial shortlist without the original component documents. Save build/test/performance findings with commands, input fingerprints, and limitations.

## 9. Later deployment

Keep the same contracts. Run preparation outside the web process, store versioned Parquet and the account-key secret in private persistent storage, and serve cached aggregate responses. Size memory and concurrency from measured queries; keep account-level fragments inaccessible to the browser. Cloud hosting, external feasibility research, reference matching, and database migration are not required for this local build.
