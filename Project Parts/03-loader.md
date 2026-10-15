# 03 — Data Loader, Processing, and Caching

**Owner:** Tinyu Xie  
**Project:** Client Metadata Outreach Prioritizer  
**Status:** Team component draft. This follows `00-vision.md` and the pandas/flat-file recommendation in `technical.md`. The implementation defaults below are proposals to reconcile with `01-design.md` and `02-data.md` before combining the team prompt.

## Purpose and boundaries

Build a loader that turns ListenBrainz listening events into reliable, reusable client-level metrics. The priority table, client detail, scenario comparison, and briefing export must use the same calculations. Read the large raw file once during preparation; dashboard interactions use prepared data.

The loader owns file access, field extraction, validation, aggregation, and caching. It returns data and diagnostics. Filter controls, ranking weights, scenario formulas, charts, and export presentation belong to the other components. Do not contact maintainers or show listener identities.

## 1. Inputs and verified facts

Resolve paths from a configurable dataset root, not a student's home directory. Use the dataset repository's `download_data.py` and `unpack_data.py` if inputs have not been downloaded and extracted; preparation must not download anything implicitly.

| Input relative to dataset root | Use |
|---|---|
| `data/listenbrainz-listens-dump-2657-20260910-000003-incremental/listens/2026/9.listens` | Initial full listening-event input; 3,966,393,313 bytes locally. UTF-8, one nested JSON object per line. One row represents one submitted listening event. |
| The same dump's `START_TIMESTAMP`, `END_TIMESTAMP`, and `SCHEMA_SEQUENCE` | Provenance and schema checks. The local collection interval is `2026-09-09 00:00:02.717236+00:00` to `2026-09-10 00:00:03.308037+00:00`; schema sequence is `1`. These are submission-window metadata, not playback filters. |
| `sample/listens_20260904.csv` | Flattened sample for development only. Mark every sample result as sample data and use a separate cache. |
| `data/listenbrainz-sample-dump-20250610-094311/lbdump/` | Optional reference data. Core client coverage metrics need no join to these files. |

Allow an explicit list of extracted `.listens` paths so later daily inputs do not require code changes. Discover files only inside selected dump directories; never combine the full input and its CSV sample.

Inspection of the first 1,000 rows of the local full input found the required nested fields, 2 syntactically valid recording MBIDs, 0 missing client names, and 990 missing client versions. This is a sequential inspection subset, not a representative estimate. The overview's 4.4-million-row count and 3.22% coverage describe a different daily file; recompute all totals for the selected inputs.

## 2. Field contract and cleaning

Extract only the following fields; tolerate absent optional keys and ignore unrelated keys. Do not flatten every field into memory.

| Prepared field | Raw JSON location | Rule |
|---|---|---|
| `user_id` | `user_id` | Nullable integer account identifier; used internally for exact distinct counts. Missing or invalid IDs do not remove listens from volume metrics. |
| `playback_date` | `timestamp` | Parse Unix seconds as a UTC datetime, then take its calendar date. Reject missing, nonnumeric, or unrepresentable timestamps and count the reason. |
| `client` | `track_metadata.additional_info.submission_client` | Trim surrounding whitespace; use a case-folded lookup key and an explicit alias map for reviewed variants. Empty, null, or non-string values become `Unknown client`. |
| `version` | `track_metadata.additional_info.submission_client_version` | Trim strings and preserve their text; use `Unknown version` for absent, blank, or non-string values. Do not parse versions as numbers. |
| `recording_mbid` | `track_metadata.additional_info.recording_mbid` | Trim and lowercase a string; validate canonical UUID syntax. Never substitute `recording_msid` or `lastfm_*_mbid`. |

The CSV sample uses `ai_submission_client`, `ai_submission_client_version`, and `ai_recording_mbid` instead of the raw nested paths. Give raw JSON and sample CSV separate input adapters that produce this same contract.

**Proposed coverage definition:** A valid recording MBID is a string matching UUID form `8-4-4-4-12` hexadecimal characters. Missing, blank, and invalid values count as lacking a usable MBID; report invalid-but-present values separately. Syntactic validity does not prove that MusicBrainz resolves the ID. Confirm this definition with the owner of `02-data.md`.

Additional rules:

- Preserve listens without a usable MBID: they are the project's opportunity measure.
- Keep unknown clients and versions in prepared data so missing metadata stays visible. Unknown clients cannot be treated as known maintainers without a reviewed mapping.
- Keep raw client-name counts in diagnostics to audit alias merges. Do not merge names through fuzzy matching.
- Put reviewed aliases and the exact list of bulk-import client keys in a small configuration file. Their contents are team data definitions, not guesses by the loader. Report unmapped keys; fail clearly if importer exclusion is requested without a reviewed list.
- Preserve historical playback dates during preparation. Apply the requested playback range at query time. Flag timestamps later than their source dump's end separately; do not silently clip timestamps.
- For malformed JSON or non-object structural blocks, skip the line, count the reason, and record its source filename and line number without logging usernames or full records. Stop with an actionable error if no usable rows remain or a dump's schema sequence is unsupported.
- Skip repeated input files by content fingerprint. Report suspected repeated events across distinct inputs; retain them unless the team defines a defensible event identity. Do not deduplicate by artist/track text or by user and timestamp alone.

## 3. Preparation and storage

Use Python's JSON reader and pandas for chunk cleaning and aggregation, and PyArrow to write compressed Parquet. Start with **10,000 raw lines per chunk**, configurable for memory limits. This draft requires no database or SQL engine.

1. Validate inputs and schema metadata. Calculate source fingerprints while scanning; record file size, timestamps, and the rules version in a manifest.
2. Read raw lines incrementally, extract the selected fields, and validate them. Discard usernames and track text immediately because the agreed views do not need them.
3. Within each chunk, group by `(playback_date, client, version, user_id)`, retaining null account IDs as a group. Write counts of `total_listens`, `with_recording_mbid`, and `invalid_recording_mbid` to Parquet fragments partitioned by playback date. Fragments may have the same group keys; queries must sum their counts across fragments.
4. Publish a cache manifest only after all fragments finish successfully. Prepare into a temporary directory; an interrupted run must not replace the last complete cache.

Store prepared fragments, the manifest, and a quality report under an application-owned `cache/` directory, outside the source data repository. Account identifiers in these fragments are internal processing data; never return these fragments to a view or include them in exports. Keep only a chunk or a compact query result in memory, not the full raw dataset or all fragments concatenated together.

## 4. Interfaces to the other components

Use typed functions with explicit inputs and no hidden global filters:

```python
prepare_data(config: LoaderConfig) -> PreparedDataset
get_client_metrics(data: PreparedDataset, filters: FilterSpec) -> pd.DataFrame
get_version_metrics(data: PreparedDataset, filters: FilterSpec,
                    client: str) -> pd.DataFrame
get_data_status(data: PreparedDataset) -> DataStatus
```

| Type | Required contents |
|---|---|
| `LoaderConfig` | Dataset root, explicit input paths and mode (`full` or `sample`), cache directory, chunk size, alias map, importer keys, and cleaning-rules version. |
| `PreparedDataset` | Completed cache location and fingerprint; source list, mode, schema/rules version, and quality-report location. No raw-event DataFrame. |
| `FilterSpec` | Inclusive UTC playback start/end dates, importer-exclusion flag, optional canonical client selection, and minimum distinct-account count. Ranking weights are not loader inputs. |
| `DataStatus` | Source filenames and submission intervals, observed playback bounds, data mode, preparation time, accepted/rejected counts, missing/invalid-field counts, future-timestamp count, and normalization/duplicate warnings. |

Return one row per canonical client with these columns. Return the same measures per version for `get_version_metrics`, including `Unknown version`.

| Column | Definition within the selected playback range and client/importer filters |
|---|---|
| `client` | Canonical submitting-client label. |
| `total_listens` | Number of accepted listening-event rows. |
| `with_recording_mbid` | Listens with a usable recording MBID under Section 2. |
| `missing_recording_mbid` | `total_listens - with_recording_mbid`. Includes invalid IDs. |
| `invalid_recording_mbid` | Listens with a nonblank but invalid recording ID; a subset of `missing_recording_mbid`. |
| `coverage` | `with_recording_mbid / total_listens`, a fraction from 0 to 1. |
| `distinct_accounts` | Distinct non-null `user_id` values among all retained listens. |
| `affected_accounts` | Distinct non-null `user_id` values with at least one missing-MBID listen. |
| `unknown_account_listens` | Retained listens without a valid account ID. |

Filter dates and importer/client keys before aggregating. Apply the minimum-account threshold after calculating client totals. When a client detail is requested, determine its eligibility from the complete client total, then return all its version groups; do not apply the minimum to each version.

Distinct accounts must be exact across chunks, dates, and versions. Read only the selected date partitions and projected columns, accumulate numeric counts incrementally, and keep sets of `(client, user_id)` and affected pairs; for version detail, also key the sets by version. Never sum daily or per-chunk distinct-user counts. Account counts across different clients or versions are also not additive.

Return empty, correctly typed tables for a valid filter with no matching rows. Treat an invalid date range as a validation error. The UI displays an empty-state message and unavailable coverage for an empty selection, not invented zero coverage.

Ranking and scenario components consume these aggregates. They must not re-read raw data or implement another definition of coverage. If an optional future join measures reference-table matching, expose it as a separate measure, never as MBID coverage.

## 5. Caching, responsiveness, and errors

Reuse a prepared cache only when source fingerprints, input mode, schema, alias/importer configuration, and cleaning-rules version match. On startup, use file path/size/modification-time checks to find candidates; rehash changed inputs and provide an explicit rebuild option. Save final hashes for reproducibility.

Cache aggregate query results by prepared fingerprint plus all filter values; Streamlit's data cache may wrap the query functions. Changing ranking weights or a scenario target reuses the same aggregates. Preparation happens explicitly once; ordinary reruns must not scan raw `.listens` files.

For missing data, report the expected path and the repository's download/unpack instructions. For permission errors, identify the inaccessible path. For corrupt or incompatible caches, explain the rebuild action. Do not substitute sample data silently. Show preparation progress and final quality counts so omitted rows are auditable.

Measure preparation time, peak memory, cache size, first filtered-query time, and repeated-query time on the target laptop. Confirm representative filters remain usable before calling the loader complete. If account sets or partition scans exceed the laptop's resources, bring measured results to the team before changing the agreed storage/query engine.

For later cloud use, run the same preparation separately, store versioned Parquet in private persistent storage, and serve cached aggregates. Change storage configuration and query internals while preserving the interfaces; keep account-level fragments inaccessible to the browser.

## 6. Build order and done-when checks

Build field extraction and validation first, then chunked preparation, then aggregate queries, then caching and the UI connection. Verify with this invented fixture, where `yes` means a syntactically valid recording UUID:

| Row | UTC date | Client | Version | Account | Valid MBID? |
|---|---|---|---|---|---|
| 1 | 2026-09-08 | Alpha | 1 | 10 | yes |
| 2 | 2026-09-08 | Alpha | 1 | 10 | no |
| 3 | 2026-09-09 | Alpha | 2 | 10 | no |
| 4 | 2026-09-09 | Alpha | unknown | 20 | yes |
| 5 | 2026-09-09 | Beta | 1 | 30 | no |
| 6 | 2026-09-09 | Bulk Importer | unknown | 40 | no |

For both dates, with `Bulk Importer` configured and excluded and minimum accounts = 1:

- Alpha: 4 listens, 2 with IDs, 2 missing IDs, coverage `0.5`, 2 accounts, 1 affected account.
- Beta: 1 listen, 0 with IDs, 1 missing ID, coverage `0.0`, 1 account, 1 affected account.
- Restricting to September 9 gives Alpha 2 listens, coverage `0.5`, 2 accounts, and 1 affected account. Minimum accounts = 2 retains only Alpha.
- Alpha's version rows are `1` = 2 listens / coverage `0.5`; `2` = 1 / `0.0`; unknown = 1 / `1.0`. Their distinct-account counts sum to 3, while Alpha has only 2 distinct accounts.

Also require these checks:

1. Process the fixture with chunk sizes 1 and 10: all returned metrics agree, including distinct and affected accounts.
2. Add separate cases for malformed JSON, missing/invalid timestamps, blank client/version, invalid UUID, and missing account ID. Verify each quality counter and that missing account IDs still contribute to listen totals.
3. Independently count a fixed raw subset line by line and compare with the prepared query for that same subset; label the subset run in its manifest. Reproduce the first-1,000-row inspection above before treating those observations as verified.
4. Assert `total_listens = with_recording_mbid + missing_recording_mbid` and `affected_accounts <= distinct_accounts` for every result. Version listen counts sum to client listen counts, including unknown versions.
5. Reconcile physical input lines as accepted rows plus rejected rows, with blank lines explicitly counted as rejected. Do not report a full-file row count until preparation completes.
6. Verify that importer exclusion, aliases, inclusive date boundaries, repeated input paths, empty selections, and sample/full cache separation behave as specified.
7. Verify that a repeated query uses the cache, changes to input/rules invalidate it, and changing ranking weights does not re-read raw data.
8. Confirm every function exposed to views returns aggregate data or status only; no account IDs or usernames appear in the interface or briefing export.

## Team alignment before combining

Confirm the proposed usable-MBID definition and reviewed alias/importer mappings with `02-data.md`; agree the UTC date convention and `FilterSpec` with `04-filters.md`; align the aggregate column names with `05-views.md`; and list pandas, PyArrow, Streamlit, and the preparation command in `06-setup.md`. No local `01-design.md` was available during this draft, so this file does not claim that DuckDB, PostgreSQL, or these implementation defaults have already received team approval.
