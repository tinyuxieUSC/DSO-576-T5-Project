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
