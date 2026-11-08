# Portable demonstration data

Derived from the course dataset_listenbrainz sample/listens_20260904.csv. All sample events and the five input fields needed by the app are retained. User names, track names, and all unused columns are omitted. Positive account identifiers are consistently replaced by sequential integers; no lookup table is retained. This is pseudonymization, not a claim of anonymity. Exact equality-based distinct and affected-account counts remain unchanged. Timestamp, client, version and recording-MBID values are unchanged.

The source is a uniform random sample of a daily submission dump, not the complete population of listeners or current client users. Playback dates include historical imports; the submission interval does not define playback dates. The cloud demo uses this sample only, not full mode. Changing the source scope can change every total, rate, eligible-client set and ranking relative to full mode. The application exposes aggregates, not event-level downloads.

Upstream: https://github.com/USC-DSO-576-PS/dataset_listenbrainz
