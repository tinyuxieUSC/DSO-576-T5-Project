# Role 3 - Data Fit

## Proposed Audiences and Decisions

### Audience A - Navidrome

A project lead at **Navidrome**, an open-source music server, must decide whether the next release cycle should prioritize better listening statistics for users or better metadata quality and MusicBrainz identifier coverage.

### Audience B - MetaBrainz Foundation

A project lead at the **MetaBrainz Foundation** must decide which scrobbling program to approach first about improving the submission of MusicBrainz recording identifiers.

## Dataset Interpretation

### What one row represents

One row in the listens table represents one track played once by one ListenBrainz account, as reported by that account's software. A row includes the user's account ID and public handle, the playback timestamp, artist and track names, usually the release name, and any additional information supplied by the reporting program. This additional information may include the submission client, music service, playback duration, and MusicBrainz identifiers.

The daily incremental file must not be interpreted as one day of actual listening. It contains listens **submitted** during a daily window, including historical listens uploaded through bulk-import tools. In the profiled file, playback timestamps range from February 13, 2005, to September 4, 2026, even though the records were submitted during one daily dump window. Therefore, any analysis of listening on a particular date must filter on `timestamp` or `listened_at_utc`.

### People, places, events, and time periods observed

- **People:** 22,516 self-selected ListenBrainz accounts appear in the profiled full daily file. These users include music enthusiasts, self-hosters, people who connected streaming accounts, and people who imported histories from services such as Last.fm. They are not representative of all music listeners, all Navidrome users, or all users of any other program.
- **Places:** Listener location is not observed. The listens table contains no listener country, city, language, or timezone. Artist country exists in a reference table, but it describes the artist rather than the listener.
- **Events:** The main table observes submitted listening events. It records what was reported as played, when it was played, and which program submitted it when that information is available. It does not directly observe feature use, recommendations shown, skipped tracks, purchase behavior, satisfaction, or user motivations.
- **Time:** The profiled file contains 4,411,662 submitted listens. Although it is one daily incremental dump, the recorded playback dates span more than 21 years because bulk imports include historical listening. The reference tables are a separate snapshot dated June 10, 2025.

## Audience A - Navidrome Project Lead

### Exact columns that could provide evidence

| Column | Potential use for the decision | Important limitation |
|---|---|---|
| `user_id` | Count distinct observed accounts and compare user reach with total listening volume. | It identifies ListenBrainz accounts, not the complete population of Navidrome users. |
| `timestamp` / `listened_at_utc` | Create time-based summaries and separate current listening from imported history. | The dump date is the submission date, so the playback timestamp must be used. |
| `artist_name`, `track_name`, `release_name` | Support basic user listening statistics by artist, track, and album. | These fields are free text and can contain inconsistent spellings or versions. |
| `ai_submission_client` | Isolate Navidrome-submitted listens and compare them with other clients. | A submission client identifies the reporting program, not necessarily the player or service in every case. |
| `ai_recording_mbid` | Measure recording-identifier coverage and support reliable joins to recording metadata. | It appears on only about 3.22% of all listens in the profiled file, although coverage is higher for Navidrome. |
| `ai_release_mbid` | Measure release-identifier coverage and support joins to release metadata. | It appears on only about 3.48% of all listens. |
| `ai_artist_mbids` | Measure whether submitted listens identify their artists reliably. | Some present values are empty arrays, so non-null does not always mean usable. |
| `ai_ms_played`, `ai_duration_ms` | Provide limited evidence about how long users listen and possible engagement. | Coverage is incomplete and some values are implausible, so explicit cleaning rules are necessary. |

### Supported by the data

The supplied data supports a **descriptive comparison** of the two development opportunities.

For listening statistics, the team can count Navidrome-submitted listens, distinct observed accounts, artists, tracks, and activity over time. These calculations can demonstrate that the observed events are technically sufficient to generate listening summaries for participating ListenBrainz accounts.

For metadata quality, the team can calculate the proportion of Navidrome listens containing recording, release, and artist MusicBrainz identifiers. It can also compare Navidrome's identifier coverage with the coverage of other submission clients.

The supplied sample contains 889 Navidrome-submitted listens from 719 accounts. Within that sample, 52.8% contain a recording MBID, 51.9% contain a release MBID, and 100.0% contain an artist MBID. These results show that identifier completeness is measurable and that missing recording and release identifiers exist in the sample. However, the sample is not the full population, so these figures should be checked against the complete daily file before being presented as general findings.

### Partly supported by the data

The data partly supports an estimate of how many observed accounts and listening events could be affected by each improvement. Account counts measure observed reach, while listen counts measure activity volume. Neither measure directly represents user value.

The data can demonstrate that listening summaries are possible, but it cannot show whether users want, notice, or regularly use those summaries. Similarly, missing identifiers reveal a metadata limitation, but they do not show how strongly that limitation affects satisfaction or retention.

The data also provides only partial evidence about Navidrome itself. It contains listens that Navidrome users submitted to ListenBrainz, rather than all listening activity from all Navidrome users. A difference between Navidrome and another client could reflect differences in their users, music libraries, configurations, or reporting behavior.

### Outside the data's scope

The supplied data cannot determine:

- whether Navidrome users prefer statistics features or metadata improvements;
- whether either feature would improve satisfaction, retention, or adoption;
- how much either option would cost or how long it would take to build and maintain;
- whether a missing identifier was caused by Navidrome, ListenBrainz ingestion, MusicBrainz coverage, or metadata in a user's own library;
- how the observed ListenBrainz-linked users differ from the complete Navidrome population;
- listener demographics or geography;
- why a user played a track or whether the track was deliberately selected, played from a playlist, or recommended;
- revenue, royalties, subscriptions, or any financial return from either investment.

### Association versus causation

This observational dataset can show associations but cannot establish causation. For example, Navidrome listens may have higher MusicBrainz identifier coverage than listens submitted by other clients. That comparison would not prove that using Navidrome causes better metadata quality. Navidrome users may differ in technical experience, library ownership, configuration, or metadata-management habits.

There was no random assignment, intervention, control group, or before-and-after test. A causal conclusion would require additional evidence, such as a controlled release experiment comparing identifier coverage or user outcomes before and after a specific Navidrome change.

## Audience B - MetaBrainz Foundation Project Lead

### Exact columns that could provide evidence

| Column | Potential use for the decision | Important limitation |
|---|---|---|
| `ai_submission_client` | Group listens by reporting program and identify high-volume programs. | Bulk importers can dominate the file and should be separated from live scrobbling clients. |
| `ai_recording_mbid` | Calculate the number and percentage of listens from each client that contain a recording MBID. | Missing values do not reveal why the identifier was absent. |
| `user_id` | Count how many distinct observed accounts use each client and avoid ranking clients only by raw listen volume. | One daily submission file does not include users who submitted nothing during that window. |
| `timestamp` / `listened_at_utc` | Separate current listening from historical imports and define the analysis period. | One incremental file cannot establish a stable long-term trend. |
| `ai_submission_client_version` | Explore whether missing identifier coverage is concentrated in particular client versions. | It is present on only about 11.82% of listens and contains inconsistent free-text versions. |
| `ai_media_player` | Provide limited additional information about the player used. | It is present on only about 2.93% of rows and may differ from the submission client. |

### Supported by the data

The data supports calculating, for each observed submission client:

- total submitted listen volume;
- number of distinct observed accounts;
- number and share of listens with a recording MBID;
- number of listens without a recording MBID; and
- concentration of missing identifiers across clients.

These measures could help MetaBrainz identify clients for which an improvement might affect many submitted listens or many observed accounts. Comparing both volume and account reach is important because a few heavy users or bulk imports can dominate total row counts.

### Partly supported by the data

The data partly supports prioritizing which client to contact. It can measure the apparent size and concentration of missing identifiers, but it cannot measure the cost of fixing each client, the maintainer's willingness or capacity to cooperate, or the technical reason identifiers are missing.

A client with many missing MBIDs may appear to offer the largest opportunity, but missing identifiers might result from users' source files, unsupported music services, or incomplete MusicBrainz catalog coverage rather than the client software itself. Multiple daily files would also be preferable before treating a client's observed volume or coverage as stable.

### Outside the data's scope

The supplied data cannot determine:

- which client maintainer is most willing or able to make a change;
- the engineering effort, financial cost, or maintenance burden of each possible integration;
- whether a missing identifier could have been supplied by the client for that specific recording;
- the exact technical cause of each missing identifier;
- how many total users each client has outside ListenBrainz;
- whether improved identifier submission would cause long-term increases in data quality, user satisfaction, or ListenBrainz adoption; or
- whether a client-level improvement would work without a pilot or controlled before-and-after evaluation.

### Association versus causation

The data can show that identifier coverage is associated with submission client, but it cannot prove that a client causes the difference. Client populations are self-selected and may differ in their technical knowledge, library sources, music catalogs, and metadata quality. A stronger causal test would introduce a specific reporting improvement for one client and compare the same quality measures before and after the change, while checking for other changes in users and submissions.

## Shared Data-Quality Risks

- **Submitted rather than played:** A daily file includes records submitted during the dump window, including historical plays.
- **Bulk-import dominance:** Import tools can contribute millions of old listens and distort client, artist, and account summaries.
- **Nonrepresentative population:** ListenBrainz accounts are self-selected enthusiasts and self-hosters; the dataset contains no population weights.
- **Missing identifiers:** Only about 3.22% of listens in the profiled file have a recording MBID, limiting clean joins to reference tables.
- **No listener geography or demographics:** The dataset cannot support demographic or geographic market segmentation.
- **Inconsistent fields:** `additional_info` has no fixed schema, and some fields contain mixed types, empty strings, empty arrays, or implausible values.
- **Free-text matching risk:** Most rows without MBIDs would require matching artist and track names as text, which can introduce false matches and missed matches.
- **Sample limitation:** The provided CSVs are random samples from different tables. Their totals are not population totals, and joins between separate samples are usually nearly empty.
- **One-day limitation:** One daily incremental file is not a stable panel and cannot show whether absent users returned later.

## Open Questions

1. Do the identifier-coverage results from the full daily file match the results observed in the sample?
2. Should the analysis include imported historical listens, or only listens actually played during the selected time period?
3. How much do the results change when the Last.fm and Archive Importers are excluded?
4. Why are recording and release identifiers missing from some Navidrome-submitted listens?
5. Do different names or versions in `ai_submission_client` refer to the same reporting program?
6. Which option do Navidrome users value more: improved listening statistics or better metadata quality?
7. Which scrobbling client maintainers have the technical ability and willingness to improve MusicBrainz identifier submission?

## Overall Data-Fit Assessment

For the Navidrome decision, the ListenBrainz data is a good fit for measuring observed listening activity and identifier completeness, but only a partial fit for choosing a release priority. The most decision-important outcomes - user demand, satisfaction, retention, development effort, and implementation cost - were not observed.

For the MetaBrainz decision, the data is a good fit for locating where missing recording identifiers are concentrated among observed submissions. It is only a partial fit for deciding whom to approach first because feasibility, cause, maintainer capacity, and expected response to an intervention are outside the dataset.

In both cases, the honest conclusion is descriptive: the data can show where patterns and data-quality gaps occur among participating ListenBrainz accounts. It cannot, by itself, prove why those patterns exist or what product decision will cause the best outcome.
