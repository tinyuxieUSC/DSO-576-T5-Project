# Change requests

Our team's log of what we found and what should change, kept in the top folder of our team repo
from Module 9 to Module 13. Pull before you edit it and push soon after.

- For each finding, copy the request template below to the end of this file, give it the next
  number and fill in every field.
- Never delete a request. When it is built, set its status to `built` with the commit; when the
  team decides against it, `declined` with the reason.
- When this file gets long, ask Codex to move the built and declined requests into a dated file
  in `change-requests-archive/` (for example `change-requests-archive/2026-11-02.md`) and leave
  only the open ones here. Numbers continue; never reuse one.

Request template:

```markdown
### CR-NN: short title

- **From:** name, YYYY-MM-DD
- **Part:** the feature, number or function
- **Evidence:** what you did and saw: the input, what you expected, what the tool gave
- **Change:** what should change, in a sentence or two
- **Priority:** high, medium or low
- **Status:** open
```

## Requests

<!-- Add new requests below this comment, at the end of the file, newest last. -->
### CR-01: Prioritize Versions by Missing MBIDs

- **From:** Zhongze Zhou, 2026-10-25
- **Part:** Client Detail feature (Part 1)
- **Evidence:** In Sample Data mode, I viewed navidrome's Client Detail page. The long version evidence table made it difficult to identify which versions had the most missing MBIDs; the table is sorted by total listens.
- **Change:** Add a concise version-level summary or chart ranked by missing recording-MBID counts so the versions with the largest gaps are easy to identify.
- **Priority:** medium
- **Status:** open

### CR-02: Show Coverage Calculation and Sample Context

- **From:** Zhongze Zhou, 2026-10-25
- **Part:** Recording-MBID coverage (Part 2)
- **Evidence:** For navidrome in Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, the app showed 889 listens, 420 without usable MBID, and 52.8% coverage. My independent check found 469 usable recording MBIDs out of 889 listens, also 52.8%. The check covers this sample, client, and date range only.
- **Change:** Show the usable-MBID count, total listens, coverage calculation and result (469 / 889 = 52.8%), sample mode and playback-date scope, and a brief data limitation together beside the coverage metric.
- **Priority:** medium
- **Status:** open

### CR-03: Compare Rankings Across Different Weights

- **From:** Gigi Zhu, 2026-10-26
- **Part:** Shortlist ranking feature (Part 1)
- **Evidence:** In Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, classified importers excluded and minimum accounts set to 100, I compared reach weights of 0%, 50% and 100%. Web scrobbler ranked fourth at 0%, while listenbrainz android ranked fourth at 50% and 100%. The Shortlist table shows only the current setting, so comparing results required screenshots.
- **Change:** Add a side-by-side comparison of all shortlisted clients’ ranks at 0%, 50% and 100% reach weight. Explain rank changes using affected-account counts and unusable-ID listen counts so users can understand how their priorities affect the recommendation.
- **Priority:** medium
- **Status:** open

### CR-04: Show the Distribution of Affected Accounts

- **From:** Gigi Zhu, 2026-10-26
- **Part:** Affected accounts (Part 2)
- **Evidence:** For navidrome in Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, the app showed 420 listens without usable recording MBIDs and 318 affected accounts. An independent raw-CSV check confirmed 318 affected accounts: 279 had exactly one unusable-ID listen and 39 had multiple. Another 401 accounts had none. The current totals do not show this distribution.
- **Change:** Add an aggregate breakdown of accounts with zero, one and multiple unusable-ID listens for the selected client and date range. This would help users distinguish a problem spread across many accounts from repeated missing IDs concentrated in fewer accounts.
- **Priority:** medium
- **Status:** open