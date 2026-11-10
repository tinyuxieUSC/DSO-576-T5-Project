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

### CR-01: Make the team run instructions portable

- **From:** Giselle Luk, 2026-10-26
- **Part:** outreach shortlist feature
- **Evidence:** `outreach-app/README.md` hard-codes `/Users/tinyux/Desktop/dso576/DSO-576-T5-Project/outreach-app` and refers to `outreach-app/.venv`, which is absent in this checkout. The shortlist therefore cannot be reproduced from the documented command on another machine.
- **Change:** Use a repository-relative command and document creation/synchronization of the team's environment from `requirements.txt`. Verify the command from a clean checkout and retain a clear missing-cache preparation message.
- **Priority:** high
- **Status:** built — portable launcher `cd45777`; repository-relative run instructions in the MVP README

### CR-02: Separate absent and invalid recording IDs in the shortlist

- **From:** Giselle Luk, 2026-10-26
- **Part:** outreach shortlist feature
- **Evidence:** The ranking uses the combined `missing_recording_mbid` value, which includes absent and populated-invalid IDs. `outreach/views.py` exposes the separate counts only in the selected client's detail view, so the shortlist user cannot compare those kinds of opportunity without opening clients one by one.
- **Change:** Add separate absent-ID and invalid-ID columns or a breakdown control to the shortlist, and explain that neither category proves client causation. Keep the combined total for the score if the team still wants it.
- **Priority:** medium
- **Status:** built — `57ee75b`

### CR-03: Show achieved coverage and the minimum additions needed to reach the target

- **From:** Tinyu Xie, 2026-10-26
- **Part:** Scenario comparison; additional tagged listens
- **Evidence:** Codex-assisted app and calculation checks, reviewed and adopted by Tinyu:  Sample mode, UTC dates 2005-02-13 through 2026-09-03, importer exclusion on, minimum accounts 100. At a 1% target, Pano Scrobbler has 520 listens and 0 valid IDs. The browser and independent raw-CSV search both return 5 rounded additions. That yields 0.9615%; a separate integer search requires 6 to reach at least 1%. The table does not show achieved post-rounding coverage. `outreach/filters.py:54` uses nearest rounding rather than a minimum-to-reach rule.
- **Change:** Keep the documented approximate scenario count, add achieved post-rounding coverage, and expose a separate minimum-to-reach count with its distinct meaning. Test both against the 520-listen, 0-valid, 1%-target case. Do not represent a hypothetical count as achievable maintainer impact.
- **Priority:** medium
- **Status:** built — `57ee75b`

### CR-04: Export the complete selected scenario comparison

- **From:** Tinyu Xie, 2026-10-26
- **Part:** Scenario comparison to briefing workflow
- **Evidence:** Codex-assisted app and calculation checks, reviewed and adopted by Tinyu:  Selected navidrome and Pano Scrobbler in Scenario comparison. At 75%, their additions were 198 and 390. Later, at the 1% target, opening Briefing with no inspected client requests a client selection; inspecting navidrome produces numerical evidence for navidrome alone even while comparison settings list both clients. `outreach/views.py:180` filters scenario evidence to the inspected client. The comparison table's seven-column data frame at line 168 has no playback dates, source mode, or warning fields.
- **Change:** Add a comparison CSV and Markdown briefing for all two or three selected clients, including observed totals/coverage, hypothetical additions, target, mode, source fingerprint, playback dates, filters, rounding interpretation, scenario limitations, and non-additive account warning. Preserve the existing single-client briefing. Verify that a two-client export contains two numerical result rows and the settings needed to reproduce them.
- **Priority:** medium
- **Status:** built — `57ee75b`

### CR-05: Prioritize Versions by Missing MBIDs

- **From:** Zhongze Zhou, 2026-10-25
- **Part:** Client Detail feature (Part 1)
- **Evidence:** In Sample Data mode, I viewed navidrome's Client Detail page. The long version evidence table made it difficult to identify which versions had the most missing MBIDs; the table is sorted by total listens.
- **Change:** Add a concise version-level summary or chart ranked by missing recording-MBID counts so the versions with the largest gaps are easy to identify.
- **Priority:** medium
- **Status:** built — `c9d8b0b`

### CR-06: Show Coverage Calculation and Sample Context

- **From:** Zhongze Zhou, 2026-10-25
- **Part:** Recording-MBID coverage (Part 2)
- **Evidence:** For navidrome in Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, the app showed 889 listens, 420 without usable MBID, and 52.8% coverage. My independent check found 469 usable recording MBIDs out of 889 listens, also 52.8%. The check covers this sample, client, and date range only.
- **Change:** Show the usable-MBID count, total listens, coverage calculation and result (469 / 889 = 52.8%), sample mode and playback-date scope, and a brief data limitation together beside the coverage metric.
- **Priority:** medium
- **Status:** built — `c9d8b0b`, wording refined in `445aa53`

### CR-07: Compare Rankings Across Different Weights

- **From:** Gigi Zhu, 2026-10-26
- **Part:** Shortlist ranking feature (Part 1)
- **Evidence:** In Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, classified importers excluded and minimum accounts set to 100, I compared reach weights of 0%, 50% and 100%. Web scrobbler ranked fourth at 0%, while listenbrainz android ranked fourth at 50% and 100%. The Shortlist table shows only the current setting, so comparing results required screenshots.
- **Change:** Add a side-by-side comparison of all shortlisted clients’ ranks at 0%, 50% and 100% reach weight. Explain rank changes using affected-account counts and unusable-ID listen counts so users can understand how their priorities affect the recommendation.
- **Priority:** medium
- **Status:** built — `c9d8b0b`

### CR-08: Show the Distribution of Affected Accounts

- **From:** Gigi Zhu, 2026-10-26
- **Part:** Affected accounts (Part 2)
- **Evidence:** For navidrome in Sample Data mode, with playback dates 2005-02-13 through 2026-09-03, the app showed 420 listens without usable recording MBIDs and 318 affected accounts. An independent raw-CSV check confirmed 318 affected accounts: 279 had exactly one unusable-ID listen and 39 had multiple. Another 401 accounts had none. The current totals do not show this distribution.
- **Change:** Add an aggregate breakdown of accounts with zero, one and multiple unusable-ID listens for the selected client and date range. This would help users distinguish a problem spread across many accounts from repeated missing IDs concentrated in fewer accounts.
- **Priority:** medium
- **Status:** built — `c9d8b0b`

### CR-09: Separate screening rank from verified outreach eligibility

- **From:** Rachel case, 2026-11-08
- **Part:** Shortlist eligibility and client classification
- **Evidence:** In Sample Data mode with playback dates `2005-02-13` through `2026-09-03`, classified-importer exclusion on, minimum accounts `100`, and reach weight `50%`, the independent sample calculation gives `listenbrainz` 1,090 listens, 765 distinct accounts, 765 affected accounts, 1,090 unusable IDs, and score `1.000`. The configuration lists exact importer and regular-client names; `listenbrainz` is in neither list and is therefore classified `unknown`. The loader excludes only `NOT_REPORTED` and clients below the account floor before ranking; `rank_clients` does not require `client_type == "regular"`.
- **Change:** Keep unknown labels visible as investigation leads, but add a clearly separate outreach-eligibility status or filter that requires verified classification and ownership. Label the current rank as screening priority and do not imply that rank alone makes an unknown client an outreach candidate.
- **Priority:** medium
- **Status:** built — `c9d8b0b`; every label remains unverified until ownership is checked outside the app
