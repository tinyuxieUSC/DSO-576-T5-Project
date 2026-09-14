# Auxiliary Data

## Stakeholder and decision

The stakeholder is a project lead at Navidrome.

The decision is whether the next release cycle should prioritize:

1. better listening statistics for users, or
2. better metadata quality and MusicBrainz identifier coverage.

The supplied ListenBrainz data provides useful evidence about listening behavior and metadata coverage, but some decision-important information is still missing.

## Option 1: Better listening statistics

### Missing information

The main missing information is direct evidence of user demand.

The ListenBrainz data shows that user-level listening summaries are technically possible, but it does not show whether Navidrome users actually want more statistics features, how important those features are to them, or whether the features would improve satisfaction or retention.

### Possible auxiliary data source

A promising source would be Navidrome user feedback.

This could come from:

- GitHub feature requests
- GitHub discussion posts
- issue comments and reactions
- a short Navidrome user survey

Navidrome developers or project maintainers would collect this information.

One row could represent one feature request, discussion post, or survey response.

Possible fields could include:

- date
- feature requested
- feature category
- number of reactions or votes
- importance rating
- satisfaction rating
- frequency of using current statistics features
- free-text comments

### Connection to ListenBrainz

This auxiliary data may not connect directly to individual ListenBrainz users.

Instead, the two sources would complement each other.

ListenBrainz could show what listening-statistics features are technically possible, while user-feedback data could show whether users actually want those features.

### New question made possible

The additional data could help answer:

Which listening-statistics features do Navidrome users value most, and is demand strong enough to justify prioritizing them in the next release?

### What could fail

GitHub users may not represent all Navidrome users. More active or technical users may be more likely to post feature requests.

A survey could also have a low response rate.

If real user-feedback data is unavailable, a small synthetic table could demonstrate the idea using fields such as feature requested, importance score, satisfaction score, and user type.

### Open question

Would GitHub feedback provide enough evidence of user demand, or would Navidrome need a separate survey before prioritizing statistics features?

## Option 2: Better metadata quality

### Missing information

The main missing information is why recording and release MusicBrainz identifiers are missing and how difficult those problems would be to fix.

The ListenBrainz sample shows that Navidrome has strong artist identifier coverage but that about half of recording and release identifiers are missing.

However, the data does not show whether the missing identifiers are caused by unavailable source metadata, matching failures, software implementation choices, or another technical problem.

### Possible auxiliary data source

A promising source would be Navidrome's GitHub repository and development records.

This could include:

- GitHub issues
- pull requests
- release notes
- developer documentation
- commit history related to MusicBrainz metadata

Navidrome developers and contributors would create this information.

One row could represent one issue, pull request, commit, or release.

Possible fields could include:

- issue or pull request ID
- date
- metadata problem category
- issue status
- affected component
- number of comments
- release version
- identifier type involved
- resolution time

### Connection to ListenBrainz

The two sources could be connected at the problem or feature level.

ListenBrainz can measure how many Navidrome listens are missing recording or release identifiers.

GitHub development data could provide evidence about the technical causes of those gaps and how difficult they may be to fix.

### New question made possible

The additional data could help answer:

Which metadata problem affects the largest share of Navidrome listens, and is the likely improvement large enough to justify the engineering effort?

### What could fail

Public GitHub activity does not fully measure engineering cost.

Some work may happen outside public issues, and a large number of comments does not necessarily mean that a problem is difficult to solve.

If real engineering-effort data is unavailable, a small synthetic table could demonstrate the idea using fields such as metadata problem, affected listen share, estimated engineering effort, and expected identifier improvement.

### Open question

What internal engineering information would Navidrome need in order to compare the cost of metadata improvements with the cost of building new listening-statistics features?