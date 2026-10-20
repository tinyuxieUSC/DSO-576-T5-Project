# Build and validation findings

Built October 20, 2026 from `../one-shot-prompt.md` on macOS ARM64 using Python 3.14.7. Input repositories were read-only; generated caches and validation inputs live under ignored `data/`.

## Validation result

`python -m pytest -q`: **21 passed** (6.98 seconds in the final run). `git diff --check` and Python compile checks passed. Both sample and full-mode Streamlit UI tests passed. The initial shortlist was also inspected in Safari at `http://127.0.0.1:8501`.

Tests cover the specified January fixture; raw/CSV parity and edge cases; exact account counts across fragments, dates, clients and versions; forced spill (including multiple version groups for one account); inclusive single-day and cross-month filtering; missing/partial weeks; scoring/ties/scenarios; configuration; input/rule/duplicate-file invalidation; failure during a write preserving the prior cache; aggregate export whitelists; fixture screen values; client selection and empty states; and UI changes without raw source reads.

## Data reconciliation

| Measure | Sample | Full |
|---|---:|---:|
| Accepted events | 21,276 | 6,780,931 |
| Rejected events | 0 | 0 |
| Distinct accounts (independent audit) | 4,060 | 23,382 |
| Valid recording UUIDs | 654 | 138,996 |
| Absent recording IDs | 20,622 | 6,641,935 |
| Populated invalid recording IDs | 0 | 0 |
| Unknown version listens | 18,814 | 6,253,926 |
| After source submission end | 0 | 20 |

The sample reconciles 21,276 parsed events with **21,278 physical lines**, including its header and quoted multiline record. The full input reconciles **6,780,931 physical lines/events**. Independent raw accumulators matched every client’s total, valid/absent/invalid-ID, distinct-account and affected-account counts for both inputs. They do not use the production adapters or grouping code.

Full source SHA-256: `8ee6665ea88f985052d76eb6eecd5d7c85d68afe6b399f0e4f473897cdfbcb48`. Its total and coverage counts reproduce the audited snapshot in the specification. All 20 events after the source end were retained and flagged.

## Measured performance

| Measurement | Sample | Full |
|---|---:|---:|
| Preparation, including hashing/compaction | 3.67 | 112.17 |
| Compaction | 1.25 | 8.42 |
| Preparation peak RSS (MiB) | 143.9 | 256.9 |
| Query-process peak RSS (MiB) | 145.4 | 236.6 |
| Prepared Parquet files | 250 | 262 |
| Prepared Parquet bytes | 1,901,988 | 4,860,107 |
| All-date query, importers included | 0.705s / 0.676s / 0.670s | 1.241s / 1.194s / 1.196s |
| Importers excluded | 0.301s | 0.734s |
| Warm Streamlit AppTest rerun: reach_weight | 0.076s | 0.074s |
| Warm Streamlit AppTest rerun: target_coverage | 0.072s | 0.073s |

The full uncached broad-range query exceeds the one-second interaction target. Warm weight/target reruns meet it in Streamlit AppTest, which executes the complete Python app after aggregate caches are warm. This is **not** browser rendering or network latency. The microsecond `aggregate_cache_hit_seconds` in JSON measures a Python memoization lookup only. No cold-disk claim is made: OS caches were not flushed, and other machine activity was not controlled. Preparation RSS is sampled every 10 ms; very brief peaks may be missed. Query RSS is measured in a separate process from full preparation. The configured query budget was 1,024 MiB.

## Storage-layout comparison

The isolated fixed subset contains **6,780 events / 3,951,744 bytes**, selecting every 1,000th physical line of the full input. SHA-256: `bc8d94624bdbce11dab933a4af3e507e3465373c1fa1705c917524df5387288a`. It uses a separate validation cache and is never represented as sample/full production results.

| Layout | Parquet files | Bytes | First / repeated query |
|---|---:|---:|---|
| date_per_chunk | 4,816 | 30,945,861 | 6.496s / 6.477s |
| compacted_month | 259 | 1,809,903 | 0.533s / 0.536s |

Date-per-chunk preparation took 3.689s; month preparation took 3.156s, including 1.470s compaction. The subset preparation process already contained prior query/audit allocations, so its RSS is not a clean process baseline; use the separate full-preparation measurement above for the production path.

All client, version and observed weekly aggregate columns matched between layouts over the broadest dates, a single day, and January 31–February 1 inclusive. An independent raw audit also matched. The layouts were measured sequentially without flushing OS caches; these subset timings are not extrapolated to full data.

## Reproduction

```bash
# From the repository root:
cd outreach-app
source .venv/bin/activate
python -m outreach.prepare --config config.toml --mode sample --rebuild
python -m outreach.prepare --config config.toml --mode full --rebuild
python -m pytest -q
python tests/validate_data.py --mode sample
python tests/validate_data.py --mode full --layout
python -m streamlit run app.py -- --config config.toml
```

The final validation-script runs refreshed the full raw audit and layout comparisons after exact Arrow predicate pushdown was added. The warm AppTest measurement selects the first eligible client, warms version/week queries, then changes reach weight to 70% and target to 85%. Direct dependency versions are in `requirements.txt` and the JSON reports.

## Input and preparation fingerprints

- Sample source: `0efdc64b6ba91b603eb412e2012a95fe14aa84b46b08ccd6e22a29e512289b35`
- Sample prepared: `d3339cdc535422b49f6a5784ec8e096c1df06027c17b9ed49aea627601debd10`
- Full prepared: `c34ba377bce92bcfb7253dbd22ae2e3da90544e4a0ddf57661dbf17d272fdf15`

Fingerprints include local policy/secret-version and source metadata, so rebuilding on another machine or with another secret produces a different preparation fingerprint. No secret or account identifiers are included in these findings.

## Practical limits

The app measures observed submissions and recording-UUID syntax, not reference matching, causality, maintainer activity or actual improvement feasibility. Unlisted client types remain unverified. The account floor does not guarantee anonymity. Account counts across clients are not additive. Very large months may produce files below the 32–128 MiB target because the bounded compaction buffer takes precedence; all current snapshot files are smaller than that target. Query memory errors report infeasible resources explicitly; this build does not establish arbitrary-input/concurrency or cloud-hosting guarantees.
