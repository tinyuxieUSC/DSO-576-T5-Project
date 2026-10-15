# 02 Data — Sources, preparation, and validation

## Purpose and boundary

Prepare reliable listening data for the Client Metadata Outreach Prioritizer. This piece owns acquisition, field mapping, cleaning, and data-quality checks. It returns queryable data and a preparation report to the loader. It does not implement rankings, scenarios, Streamlit screens, or outreach.

This is a proposed specification based on the supplied dataset README, not a report of completed data analysis. Verify source fields and record the findings before treating the contract as build-ready.

## Inputs and acquisition

- Dataset repository: `USC-DSO-576-PS/dataset_listenbrainz`.
- Read `data_overview_listenbrainz.md` and `sample/README.md`, then inspect sample rows to confirm table meanings and source fields.
- Use the repository's `download_data.py` and `unpack_data.py` instructions. Verify publisher checksums. If scripted downloads fail, use the overview's browser route.
- Inspect both downloaded archives. Use only tables required for this tool; do not join reference tables unless their role and join keys are established. Check join-key uniqueness before any join that could multiply listens.
- Keep downloaded files and generated data out of git. Do not modify the read-only dataset repository.

The README reports approximately 4.4 million plays from 22,516 accounts in the profiled daily file, a 246.7 MB reference archive, roughly 450–650 MB total download, and about 6 GB of unpacked disk space. These are reference figures, not measured sizes of our selected analysis tables or RAM requirements.

## Output contract

Write `data/prepared/listens.parquet`, with one row per retained source listen. These are proposed output names, not assumed source-field names:

| Column | Meaning |
|---|---|
| `played_at_utc` | Playback timestamp normalized to UTC |
| `account_key` | Stable internal account key for distinct counts; nullable |
| `client_name` | Submitting software identity; nullable when unknown |
| `client_version` | Reported version; nullable |
| `recording_mbid_status` | `valid`, `missing`, or `invalid` for the submitted recording identifier |
| `client_type` | `regular`, `importer`, or `unknown`, from explicit classification rules |

Also write `data/prepared/preparation-report.json` with source filenames and checksums, field mappings, actual row counts and file sizes, playback-date bounds, rejected-row counts and reasons, field-quality counts, and preparation/classification versions. The loader receives these paths; it must not need to repeat cleaning rules.

## Cleaning and interpretation rules

1. **Confirm provenance.** Map the submitting-client field separately from the player and streaming service. Identify the directly submitted recording MBID field; do not silently substitute a release MBID, recording text, or an identifier inferred by another service. If provenance cannot be established, report it as a blocking issue.
2. **Playback dates.** Use playback time for filtering, rather than download date or submission time. Reject rows with absent or unparseable playback timestamps from the prepared analysis table and report their count. Report actual playback bounds; a daily export does not imply every playback occurred that day.
3. **Client identity.** Trim surrounding whitespace and convert empty names to null. Merge aliases only through an explicit mapping backed by inspected values. Preserve unknown clients; do not guess identities from service names. Keep version missingness visible.
4. **Recording identifiers.** Treat absent, null, or empty values as `missing`. Check populated values against the documented recording-MBID representation and UUID syntax; classify malformed values as `invalid`. Syntactic validity does not establish that an identifier exists in MusicBrainz. Keep missing and invalid counts separate. The proposed coverage definition counts only syntactically valid submitted identifiers.
5. **Accounts.** Preserve one stable internal key across dates and files. Missing account keys remain null, contribute to listen counts, and are excluded from distinct-account counts. Report this limitation. Never pass account keys to display tables or exports.
6. **Importer classification.** Store evidence-backed client classifications in one configuration file. Unrecognized clients stay `unknown`; absence from the importer list does not prove regular-client status. Classification alone also does not prove current activity. Downstream screens must make the observation period and unknown classifications visible.
7. **Duplicates.** Check for overlapping inputs and repeated source events. Do not remove rows solely because account, track, and timestamp match. Use a documented stable event identifier when available; otherwise require an explicit overlap policy before combining files that may repeat events.
8. **Preserve flexibility.** Keep sufficient row-level information internally for playback-date filtering, client-version breakdowns, and account deduplication across dates. Do not replace it with daily distinct-account totals, which cannot safely be summed.

## Preparation and runtime

Run preparation once per new source snapshot or cleaning-rule change. Process large files in batches or through DuckDB rather than assuming all raw data fits in pandas memory. Persist the prepared Parquet data on disk. The loader can query it with DuckDB and return aggregates to the application; ranking and scenario calculations belong to their own pieces.

## Done when

- Actual input/output row counts, compressed and prepared file sizes, playback bounds, and missingness statistics are recorded in the preparation report.
- Retained rows plus rejected rows reconcile to input rows, with any verified duplicate removals accounted for separately. Preparation does not silently multiply rows.
- Every retained row has a parseable UTC playback timestamp; status and client-type values belong to their declared categories.
- A small source sample independently agrees with prepared client identities, account keys, timestamps, and recording-MBID classifications.
- A two-date fixture with account A missing an MBID on both dates, B missing one on the second date, and C always having a valid MBID produces 3 distinct accounts and 2 affected accounts across both dates. This is an expected check, not a claim that a test has been run.
- Missing/invalid MBIDs, unknown clients, missing versions, and missing account keys are reported rather than silently dropped or guessed.
- A representative date-filtered query has measured runtime and peak memory recorded. If performance is unsuitable on the team's laptop, revise the storage/query plan before integrating the UI.

## Decisions to confirm with the team

- Verify the exact source fields, identifier representation, and any required reference-table joins.
- Agree on importer evidence, the treatment of unknown clients, and an explicit definition of an active client.
- Confirm whether malformed identifiers belong in the outreach opportunity alongside missing identifiers; keep their counts separate regardless.
- Confirm the source snapshot, overlap policy, and supported playback-date range.
