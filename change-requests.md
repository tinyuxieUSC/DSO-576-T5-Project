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
- **Status:** open

### CR-02: Separate absent and invalid recording IDs in the shortlist

- **From:** Giselle Luk, 2026-10-26
- **Part:** outreach shortlist feature
- **Evidence:** The ranking uses the combined `missing_recording_mbid` value, which includes absent and populated-invalid IDs. `outreach/views.py` exposes the separate counts only in the selected client's detail view, so the shortlist user cannot compare those kinds of opportunity without opening clients one by one.
- **Change:** Add separate absent-ID and invalid-ID columns or a breakdown control to the shortlist, and explain that neither category proves client causation. Keep the combined total for the score if the team still wants it.
- **Priority:** medium
- **Status:** open

### CR-03: Show achieved coverage and the minimum additions needed to reach the target

- **From:** Tinyu Xie, 2026-10-26
- **Part:** Scenario comparison; additional tagged listens
- **Evidence:** Codex-assisted app and calculation checks, reviewed and adopted by Tinyu:  Sample mode, UTC dates 2005-02-13 through 2026-09-03, importer exclusion on, minimum accounts 100. At a 1% target, Pano Scrobbler has 520 listens and 0 valid IDs. The browser and independent raw-CSV search both return 5 rounded additions. That yields 0.9615%; a separate integer search requires 6 to reach at least 1%. The table does not show achieved post-rounding coverage. `outreach/filters.py:54` uses nearest rounding rather than a minimum-to-reach rule.
- **Change:** Keep the documented approximate scenario count, add achieved post-rounding coverage, and expose a separate minimum-to-reach count with its distinct meaning. Test both against the 520-listen, 0-valid, 1%-target case. Do not represent a hypothetical count as achievable maintainer impact.
- **Priority:** medium
- **Status:** open

### CR-04: Export the complete selected scenario comparison

- **From:** Tinyu Xie, 2026-10-26
- **Part:** Scenario comparison to briefing workflow
- **Evidence:** Codex-assisted app and calculation checks, reviewed and adopted by Tinyu:  Selected navidrome and Pano Scrobbler in Scenario comparison. At 75%, their additions were 198 and 390. Later, at the 1% target, opening Briefing with no inspected client requests a client selection; inspecting navidrome produces numerical evidence for navidrome alone even while comparison settings list both clients. `outreach/views.py:180` filters scenario evidence to the inspected client. The comparison table's seven-column data frame at line 168 has no playback dates, source mode, or warning fields.
- **Change:** Add a comparison CSV and Markdown briefing for all two or three selected clients, including observed totals/coverage, hypothetical additions, target, mode, source fingerprint, playback dates, filters, rounding interpretation, scenario limitations, and non-additive account warning. Preserve the existing single-client briefing. Verify that a two-client export contains two numerical result rows and the settings needed to reproduce them.
- **Priority:** medium
- **Status:** open
