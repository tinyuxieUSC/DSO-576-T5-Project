# Technical Path — ListenBrainz

## Download result

I followed the provided ListenBrainz download instructions using:

```bash
uv run python download_data.py
```

The download completed successfully and saved two archives into the local `data` folder.

| File | Format | Size | Result |
|---|---|---:|---|
| `listenbrainz-listens-dump-2657-20260910-000003-incremental.tar.zst` | compressed `.tar.zst` archive | 304.9 MB | Downloaded successfully in 63 seconds; SHA-256 checksum OK |
| `listenbrainz-sample-dump-20250610-094311.tar.zst` | compressed `.tar.zst` archive | 246.7 MB | Downloaded successfully in 46 seconds; SHA-256 checksum OK |

Total downloaded size reported by the script: about **552 MB**.

No download errors or checksum problems occurred.

The archives are compressed with Zstandard inside a tar archive, so they are not intended to be opened directly by double-clicking. The provided next step is:

```bash
uv run --with zstandard python unpack_data.py
```

At the time of this write-up, the download itself is verified. The full archives still need to be unpacked before the complete raw data can be inspected locally.

## Files I was able to open

I also checked the provided CSV sample files in pandas. They opened successfully with `pd.read_csv`; for the listens sample, `dtype=str` is appropriate because some columns contain mixed types.

Examples checked successfully include:

- `listens_20260904.csv` — 21,276 rows x 56 columns, about 8.16 MB
- `meta_artists.csv` — 5,549 rows x 13 columns, about 2.41 MB
- `meta_artist_release_groups.csv` — 7,692 rows x 9 columns, about 2.54 MB
- `meta_release_groups.csv` — 2,408 rows x 18 columns, about 2.45 MB
- `meta_release_group_recordings.csv` — 8,038 rows x 8 columns, about 2.48 MB
- `meta_recordings.csv` — 2,236 rows x 21 columns, about 2.49 MB
- `spark_artist_country_code.csv` — 5,565 rows x 3 columns, about 0.29 MB
- `spark_artist_credit.csv` — 49,019 rows x 4 columns, about 2.54 MB
- `spark_artist_genre.csv` — 50,000 rows x 3 columns, about 2.52 MB
- `spark_artist_tag.csv` — 50,000 rows x 3 columns, about 2.51 MB
- `spark_recording_artist.csv` — 11,574 rows x 3 columns, about 2.54 MB
- `pop_top_recording.csv` — 31,645 rows x 4 columns, about 2.51 MB
- `pop_release_group.csv` — 13,586 rows x 3 columns, about 0.59 MB
- `pop_mlhd_top_recording.csv` — 30,864 rows x 4 columns, about 2.52 MB

The files `pop_recording.csv`, `pop_mlhd_recording.csv`, and `pop_mlhd_release_group.csv` also opened successfully, but contain only headers and zero data rows. This is expected from the source and is not a download failure.

These CSVs are samples, not the full population data. They are useful for learning the table structure and testing code, but totals or rankings from the samples should not be presented as full-data findings.

## Technical characteristics that matter

The main ListenBrainz daily file is large. The data overview profiles a daily file with roughly **4.4 million listening events and 56 columns**. The fixed reference download contains many additional metadata and popularity tables.

One important issue is that a daily dump represents listens **submitted** during a particular day, not necessarily listens **played** on that day. Bulk imports can add listening history from previous years. Any analysis about actual listening behavior on a specific date should therefore use the playback timestamp rather than treating every row in a daily dump as a play from that day.

A second technical issue is joining the listening table to the reference data. Only a small portion of listens contain the MusicBrainz recording identifier needed for a clean key-based join. Rows without that identifier would require matching artist and track names as text, which would add cleaning work and possible matching errors.

## Flat files or PostgreSQL?

### Flat files

For the current stage, I recommend starting with **flat files plus pandas**.

Reasons:

- No database installation is required.
- The provided sample files are already easy to open and inspect.
- CSV and Parquet are well supported by pandas.
- Parquet is compressed and efficient for the reference tables.
- We can test ideas on samples or subsets before processing the full data.
- The team is still deciding what analysis and output are actually needed.

The main limitation is memory. The full listening file should not be loaded into pandas all at once. A better approach is to process it incrementally, keep only the columns needed, and create summaries while reading.

### PostgreSQL

PostgreSQL becomes more useful if the project later needs:

- multiple daily listening dumps;
- repeated joins across many reference tables;
- repeated queries by several teammates;
- regularly refreshed data;
- a shared database for a deployed application; or
- more data than is comfortable to manage with local flat files.

Because ListenBrainz has one large event table and many related reference tables, PostgreSQL is a realistic later option. However, setting it up now would add complexity before we know whether we need it.

**Current recommendation:** start with flat files and pandas. Reconsider PostgreSQL if the final scope expands to multiple days, repeated joins, or a shared/deployed system.

## Course tools that may help

**pandas** is the most useful tool immediately. It can load CSV and Parquet files, filter rows, clean fields, group listening events, and create summaries.

**Plotting packages** will be useful for exploratory analysis and communicating findings after the team chooses a question.

**SQL / PostgreSQL** may become useful if we move beyond a small number of files or need repeated joins and shared queries. No database installation is needed yet.

**Streamlit** could be useful later if the final result is an interactive dashboard or data-oriented web application. It would provide the interface, not the storage layer.

**Supabase** could provide hosted PostgreSQL later if a deployed app needs a shared database. It is unnecessary at the current stage.

**scikit-learn** is only relevant if our eventual question requires prediction, classification, clustering, or another machine-learning method. We should not add machine learning unless the question actually requires it.

**Google Cloud / Gemini** are possible later options if the project requires cloud computing or programmatic AI, but neither is required now.

## What the team should investigate next

1. Finish unpacking the two downloaded archives and verify the expected raw files are present.
2. Decide the exact audience and decision the project is trying to support.
3. Identify which columns and reference tables are actually necessary for that decision.
4. Decide whether one daily dump is enough or whether the analysis needs multiple days.
5. Test the proposed analysis on the sample files or a limited number of raw rows before processing millions of records.
6. Check how many relevant listening rows contain MusicBrainz IDs before depending on metadata joins.
7. Estimate memory and processing time for the planned analysis and avoid loading the full raw listening file into memory at once.
8. Decide whether the final output should be a static analysis, a dashboard, or an application.
9. If the final output shows user-level data, decide whether public usernames are necessary or whether results should be aggregated or anonymized.

## Current technical recommendation

The simplest and most appropriate path right now is to use the provided **flat files with pandas**, work first with the sample data, and process the large raw listening file incrementally after unpacking it. PostgreSQL should only be added if the project expands to multiple daily dumps, repeated joins, shared queries, or deployment. Streamlit can be considered later if an interactive interface would help the chosen audience. No database installation, cloud account, deployment, or model training is required at this stage.
