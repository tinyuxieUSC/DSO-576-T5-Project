# Project Objective

## Stakeholder and decision

The stakeholder is a project lead at **Navidrome**, an open-source music server.
They must decide whether the next release cycle should prioritize:

1. better listening statistics for users, or
2. better metadata quality and MusicBrainz identifier coverage.

## Primary objective

Use the public ListenBrainz listening data and reference tables to determine which
investment would create more value for Navidrome users: expanding statistics
features or improving metadata quality. The analysis should identify the size of
each opportunity, explain which users or listening programs are most affected,
and provide an evidence-based release recommendation.

## Analytical objectives

- Measure listening activity by reporting program, account, artist, recording,
  and time period to estimate demand for richer statistics.
- Quantify metadata completeness and identifier coverage, especially the share
  of listens that can be connected reliably to MusicBrainz entities.
- Compare the two opportunities using user reach, listening volume, and the
  likely concentration of the problem rather than relying only on total row
  counts.
- Identify meaningful differences across scrobbling programs and user segments
  so Navidrome can target the highest-impact improvements.
- State the data limitations clearly, including that ListenBrainz users are not
  representative of all Navidrome users and that public listens do not directly
  measure feature demand or satisfaction.

## Decision deliverable

Recommend one release priority, supported by reproducible measures and concise
visual evidence. If the evidence does not clearly favor one option, propose a
sequenced or small pilot release and specify what additional information Navidrome
should collect before making a larger investment.

## Analysis and findings

The analysis uses the supplied ListenBrainz sample file, which contains 21,276
listens from 4,060 accounts.

### Listening-statistics opportunity

- 1,089 accounts (26.8%) appear more than once, so user-level summaries are
  technically feasible.
- Each account contributes an average of 5.2 listens and 5.0 distinct recording
  identifiers.
- The most-played artist is BTS with 1,036 listens. The most-played recording
  title is *SWIM* with 185 listens.
- The busiest month is September 2026 with 6,106 listens. The busiest UTC hour
  is 15:00 with 1,231 listens.

These results demonstrate that Navidrome could support listening summaries, but
the public data does not measure feature demand, user satisfaction, retention,
or the cost of building those features.

### Metadata-quality opportunity

| Coverage measure | All listens | Navidrome listens |
|---|---:|---:|
| Recording MusicBrainz ID | 3.1% | 52.8% |
| Artist MusicBrainz ID | 5.3% | 100.0% |
| Release MusicBrainz ID | 3.3% | 51.9% |

The sample contains 889 Navidrome-submitted listens from 719 accounts. Navidrome
has strong artist identifier coverage, but approximately half of its listens lack
recording or release identifiers. This limits reliable joins to reference
metadata and also reduces the quality of future listening statistics.

Identifier coverage varies substantially by reporting program. The largest
programs in the sample are ListenBrainz lastfm importer v2 (10,477 listens),
ListenBrainz Archive Importer (6,031), and listenbrainz (1,090), while Navidrome
accounts for 889 listens.

## Recommendation

Prioritize a targeted metadata-quality pilot in the next release, focused on
capturing or matching the missing recording and release MusicBrainz identifiers
for Navidrome listens. This should be a narrow integration and matching
improvement rather than a broad metadata rewrite because artist coverage is
already strong.

Listening statistics should follow as a smaller experiment or a subsequent
release. After the pilot, Navidrome should measure identifier match rate,
metadata correction rate, statistics-page usage, and retention or satisfaction.

## Limitations

- ListenBrainz users are not necessarily representative of Navidrome users.
- A missing identifier may reflect an ingestion or matching problem; this sample
  cannot distinguish the cause.
- The sample is descriptive evidence and does not directly establish user demand
  for either investment.
