# 04 Filters

## Job
Turn the loaded aggregate table and the user's settings into per-client metrics, a ranked shortlist, a client-version breakdown, rank sensitivity and scenario estimates. Pure pandas functions: no Streamlit, no file access, no account-level output. This keeps the piece buildable in one agent session, testable alone, and makes the privacy rule checkable at one boundary.

**Place in the design:** Prepare → Load → **Filters** → View. Setup is read by all. Filters receives the validated table from Load, settings from View, and defaults and constants from Setup. It returns only aggregate DataFrames, dicts and strings to View.

## Input table (produced by Prepare, validated by Load)
Grain: one row per (`account_key`, `client`, `client_version`, `play_date`). The key must be unique.

| Column | Type | Meaning |
|---|---|---|
| `account_key` | str | Salted hash of the account id. Never output. |
| `client` | str | Normalized `ai_submission_client`. Null or blank becomes `NOT_REPORTED` (Setup). |
| `client_version` | str | Trimmed `ai_submission_client_version`. Null or blank becomes `NOT_REPORTED`. Free text, never parsed. |
| `play_date` | date | UTC date of `timestamp` (play time, not submission day). |
| `listens` | int ≥ 1 | Listens in the group. |
| `missing_mbid_listens` | int, 0..`listens` | Listens whose `ai_recording_mbid` is null or `""`. |
| `is_bulk_importer` | bool | Setup's importer rule, applied in Prepare. |

Account-level rows are needed because distinct accounts are not additive across dates or versions: they must be counted after filtering.

## Settings (from View; defaults and limits from Setup)
| Name | Type | Rule |
|---|---|---|
| `date_start`, `date_end` | date, inclusive | `None` means the table's min and max `play_date`. |
| `exclude_importers` | bool | Default from Setup. |
| `min_accounts` | int | Effective value is `max(min_accounts, MIN_ACCOUNTS_FLOOR)`. The floor stops small-count rows about a handful of people. |
| `reach_weight` | float 0..1 | Weight on affected accounts. `1 - reach_weight` goes to missing-MBID volume. |
| `target_coverage` | float 0..1 | Scenario target. |

## Functions
| Function | Returns |
|---|---|
| `select_rows(table, s)` | Rows with `play_date` in range and, if `exclude_importers`, `is_bulk_importer == False`. |
| `client_metrics(rows, s)` | One row per client with at least the effective `min_accounts` accounts: `client, is_bulk_importer, total_listens, accounts, affected_accounts, missing_listens, coverage, first_play_date, last_play_date`. |
| `rank_clients(metrics, s)` | `metrics` without `UNRANKABLE_CLIENTS` (Setup), plus `score` and `rank` (1 is best), sorted by `rank`. |
| `rank_sensitivity(metrics, weights)` | One row per ranked client, one rank column per weight in `weights`. |
| `version_breakdown(rows, client)` | One row per `client_version` for that client, sorted by `listens` descending: `client_version, listens, missing_listens, accounts, coverage`. `NOT_REPORTED` is kept as a row. |
| `estimate_scenario(metrics, client, target)` | `dict(client, current_coverage, target_coverage, additional_tagged_listens)`. |
| `assumptions(s, rows)` | List of plain-language lines for the screen and the briefing. They state each setting in force, every definition below, and these evidence gaps: the share of listens with `NOT_REPORTED` client and with `NOT_REPORTED` version, and the observation period. Wording comes from Setup's text constants. |

## Definitions
- `total_listens` = sum of `listens`.
- `missing_listens` = sum of `missing_mbid_listens`.
- `coverage` = `1 - missing_listens / total_listens`.
- `accounts` = distinct `account_key` per client after filtering. An account using two clients counts once for each.
- `affected_accounts` = accounts with at least one missing-MBID listen in the selection.
- **Score**, with `norm(x) = log1p(x) / log1p(max over ranked clients)` (0 when the max is 0):
  `score = reach_weight * norm(affected_accounts) + (1 - reach_weight) * norm(missing_listens)`.
  The log scale stops a few heavy users or one bulk import from dominating while still rewarding larger clients.
- **Rank order:** `score` descending, then `missing_listens` descending, then `client` ascending, so the order is stable.
- **Scenario:** `additional_tagged_listens = round(max(0, target * total_listens - (total_listens - missing_listens)))`. It assumes the same listens, accounts and period as observed and that the target applies to all of the client's listens. It is a what-if, not a forecast.

## Assumptions, edge cases and data quality
- On load, assert the columns and types above, the unique key, `1 ≤ listens`, and `0 ≤ missing_mbid_listens ≤ listens`. Fail with a clear message. This also removes any divide-by-zero.
- Assert that no two `client` values collide after `strip().casefold()`. Client names are free text with case and URL variants, and normalizing them is Prepare's job.
- Importers dominate raw volume, so `exclude_importers` defaults on (Setup). Importer rows are removed whole; no other row of the same account is touched.
- `NOT_REPORTED` client rows count in `client_metrics` but are excluded from ranking, since no maintainer can be contacted.
- A client with huge volume from one account is handled by the account floor, not by special cases.
- An empty selection returns empty DataFrames with the same columns. View shows a message; no exception.
- `target_coverage` at or below current coverage gives 0.
- The data is submitted listens in the dump windows, not all listening. A missing MBID does not prove the client is at fault. `assumptions()` always says both.
- Output never contains `account_key` or any column derived one-to-one from an account. Test for it.

## Technical
- **Tool:** pandas, vectorized `groupby`, with `nunique` for accounts. No SQL; the aggregate fits in memory. Raw listens never reach this piece.
- **Memory and cache:** Load holds the table once in memory, cached. Filters is stateless and recomputes on each click, targeting under about one second. View may cache `select_rows` on (dates, importer flag).
- **Size:** Prepare reports the aggregate's row count and MB. If it is too slow, Prepare coarsens `play_date` to week or month. Filters does not change.
- **Cloud later:** nothing to change, because Filters has no files, state or environment access.

## Build order and done when
Build in this order; each step passes its check before the next.

1. `select_rows`, `client_metrics`
2. `rank_clients`
3. `version_breakdown`
4. `estimate_scenario`
5. `rank_sensitivity`, `assumptions`

**Fixture** (save as a test table; `MIN_ACCOUNTS_FLOOR=1` in tests):

| account_key | client | client_version | play_date | listens | missing_mbid_listens | is_bulk_importer |
|---|---|---|---|---|---|---|
| a1 | Alpha | 1.0 | 2026-01-01 | 10 | 10 | F |
| a1 | Alpha | 1.0 | 2026-01-02 | 5 | 5 | F |
| a2 | Alpha | 1.1 | 2026-01-02 | 10 | 0 | F |
| a3 | Alpha | 1.1 | 2026-01-03 | 5 | 5 | F |
| a10 | Alpha | 1.1 | 2026-01-03 | 1 | 1 | F |
| a4 | Beta | 2.0 | 2026-01-01 | 100 | 100 | F |
| a5 | Beta | 2.0 | 2026-01-02 | 40 | 20 | F |
| a6 | Beta | 2.0 | 2026-02-01 | 10 | 10 | F |
| a7 | Imp | 1 | 2026-01-01 | 1000 | 1000 | T |
| a8 | Imp | 1 | 2026-01-02 | 1000 | 1000 | T |
| a9 | Solo | 1 | 2026-01-01 | 500 | 500 | F |

**Settings A:** 2026-01-01 to 2026-01-31, `exclude_importers=True`, `min_accounts=2`, `reach_weight=0.5`.

| Check | Expected |
|---|---|
| `client_metrics`, Alpha | listens 31, accounts 4 (a1 counted once), affected 3, missing 21, coverage 0.3226, 2026-01-01 to 2026-01-03 |
| `client_metrics`, Beta | listens 140, accounts 2, affected 2, missing 120, coverage 0.1429 |
| Imp and Solo | Absent (importer excluded; one account below `min_accounts`) |
| `exclude_importers=False` | Imp appears: listens 2000, accounts 2, affected 2, coverage 0 |
| `date_end=2026-02-28` | Beta: listens 150, accounts 3, missing 130 |
| `rank_clients`, weight 0.5 | Beta 1 (score 0.896), Alpha 2 (0.822) |
| `rank_sensitivity`, weights 0, 0.5, 1 | Beta, Beta, Alpha first (rank flips) |
| `version_breakdown`, Alpha | 1.1: 16 listens, 6 missing, 3 accounts, coverage 0.625; 1.0: 15, 15, 1, 0 |
| `estimate_scenario`, target 0.8 | Alpha 15, Beta 92 |
| `estimate_scenario`, Beta target 0.1 | 0 |
| Any output column | None contains `account` |

**Real-data check** (full range, importers included, floor and `min_accounts` 1): the sum of `total_listens` equals the rows-kept count Prepare reports and an independent `SUM(listens)` on the aggregate. `1 - missing/total` equals coverage counted separately on the raw file (null or empty `ai_recording_mbid`) over the same rows.