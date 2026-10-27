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
