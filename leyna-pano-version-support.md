# Case: Morgan, a Pano Scrobbler maintainer, and older-version compatibility

> Working case. The earlier Navidrome version-investigation idea is withdrawn because Zhongze's case on `case-live-evidence` covers choosing a Navidrome version to investigate for unusable recording IDs. This is a different proposed decision: whether observed use of older Pano versions justifies investigating compatibility needs before the maintainer decides where to spend support work. Parts 4 and 5 remain Leyna's judgments. The final hand-in belongs in a separate `leyna-pano-version-support-final.md` and PDF.

## 1. The person and the decision

Morgan is a fictional Pano Scrobbler maintainer reviewing where to spend limited compatibility and debugging time. Morgan must decide whether the app's version-level ListenBrainz evidence is enough to investigate support needs for an older Pano release before deciding whether to keep devoting support work to it. A poor decision could leave a real compatibility problem unexplored or spend effort on a version whose observed traffic does not reflect current users or support demand.

## 2. Morgan's real situation and alternatives

Pano's official release notes show changes and fixes attached to numbered releases, while its public issue tracker records version-specific reports. In one report, a user said AutoShazam detections stopped scrobbling after Pano updated to 3.38, and that 3.37 still worked; the maintainer replied that a fix would come in the next update. This is evidence that a version-specific report can be investigated, not evidence that an older Pano release currently needs support or that ListenBrainz traffic measures the support burden.

ListenBrainz documents `submission_client_version` as the version of the software submitting a listen. That makes the version field relevant to Morgan's screening question. Morgan's alternatives are to inspect release notes and issue reports, reproduce the behavior on the relevant Pano build and operating system, review support requests and logs, and ask affected users for details. The app can summarize observed submissions but cannot replace these checks.

**Sources:**

- [Pano Scrobbler releases](https://github.com/kawaiiDango/pano-scrobbler/releases), Pano Scrobbler's official GitHub repository: release notes are organized by version and include fixes and behavior changes.
- [Version 3.38 not scrobbling from Shazam](https://github.com/kawaiiDango/pano-scrobbler/issues/488), Pano Scrobbler's official issue tracker: a user reported that AutoShazam detections stopped scrobbling after an update to 3.38 and said 3.37 worked; the maintainer replied that a fix would be in the next update.
- [JSON Documentation](https://listenbrainz.readthedocs.io/en/latest/users/json.html), ListenBrainz documentation: defines `submission_client_version` as the version of the client submitting the listen and distinguishes client-submitted IDs from server-resolved mappings.

## 3. The app in use

**Live link:** [Client Metadata Outreach Prioritizer](https://appapppy-mdilrzqijilc29whq52tc2.streamlit.app/). This is the URL printed in Gigi's example PDF. I could not open it with the available browser tool, so the current public deployment still needs to be checked.

**What Morgan selects:** In the live app, choose the displayed playback-date range and record it here. Select `pano scrobbler` for client detail; record whether classified importers are excluded and the minimum-account setting. Inspect the version table and weekly playback evidence. Keep the screenshot's settings visible.

**Live-app screenshot:** Still needed. Capture the public app itself and save it as `screenshots/pano-version.png` beside this case. Do not use a local run or recreate the screen.

**What the app shows, according to the code:** The client-detail view displays Pano's aggregate listen and account measures, MBID coverage, a version breakdown, weekly playback evidence, and ranking sensitivity. Version labels are preserved as free text; the view reports what share of Pano listens have a reported version. Weekly counts use UTC weeks, and partial edge weeks are flagged. These are observed ListenBrainz submissions under the selected filters, not a count of all installed Pano versions, a support-ticket rate, or a measure of compatibility costs.

## 4. Reading the result for Morgan's decision

**Does the number measure what Morgan cares about?** Leyna: say whether observed ListenBrainz listens by reported version are useful for deciding which compatibility question to investigate. The rows contain neither version-specific support requests nor the cost of supporting a release. The number can indicate observed use in this sample, but decide whether it measures Morgan's actual decision well enough.

**Who is in the rows, and who is not?** Leyna: describe the selected ListenBrainz submissions and filters, then identify a relevant group missing from them. The app's stated limitation is that observed submissions are an incomplete sample of playback history and client users. Version labels can also be unknown, and the app's own view says the version strings remain free text.

**What outside the data matters to this decision?** Leyna: decide which additional evidence matters for Morgan. Candidates include Pano's release notes and issue reports, current support requests, operating-system versions, reproducible tests on older builds, the maintainer's available time, and whether affected users can upgrade.

**What could Morgan wrongly conclude from it?** Leyna: name a tempting but unsupported conclusion. A version's observed ListenBrainz traffic alone cannot show that the release is compatible, unsupported, costly to maintain, or still used by all Pano users. Choose the misleading reading that matters most to Morgan and explain why the evidence does not support it.

**Code evidence:** `outreach/loader.py` groups version evidence by the submitted `client_version` text and computes listen/account aggregates. `outreach/views.py` labels version strings as free text, displays known-version share, and presents weekly evidence. Add the live screenshot's actual values and any check you run; no Pano-specific result number has been inserted here.

## 5. The verdict: prove or break

Leyna: compare the app with Morgan's alternatives in part 2. Decide whether Morgan is better off using the version detail to choose what to investigate, and state what Morgan must not conclude from the chart. Then either show why the app is as good as possible for this screening decision with its available data, or write a generalizable team change request. Do not turn the app's sampled version counts into a support policy without your own reasoning and evidence.

```markdown
Add a change request only if Leyna decides one is justified and writes it in the team's required format. Otherwise remove this box from the final memo.
```
