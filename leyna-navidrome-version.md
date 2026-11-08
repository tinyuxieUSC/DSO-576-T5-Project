# Case: Sam, a Navidrome maintainer, and version-specific recording IDs

> Working case. The person and decision below claim a different use of the team's app from Gigi's shortlist-ranking case. Parts 4 and 5 need Leyna's own judgment. The final hand-in should be a separate `leyna-navidrome-version-final.md` PDF export after the live-app evidence and answers are complete.

## 1. The person and the decision

Sam maintains Navidrome, a self-hosted music server that can send listens to ListenBrainz. During release planning, Sam must decide whether the version-level evidence is strong enough to investigate recording-ID submission for one Navidrome version before spending engineering time on a fix. A poor decision could spend a release cycle on an apparent data gap that is actually caused by users' music libraries, missing version labels, or the limits of the ListenBrainz sample.

## 2. Sam's real situation and alternatives

Navidrome's documentation explains how to enable ListenBrainz scrobbling, and its release history shows the project tracks changes and fixes across releases. Those are practical alternatives for Sam: inspect Navidrome's own release notes and issue tracker, reproduce submissions on a test installation with tagged and untagged files, and consult maintainers or users before changing the code. The ListenBrainz data can help Sam spot a version worth investigating, but the observed listens do not say whether a particular release caused an identifier gap or whether a fix is feasible.

ListenBrainz defines `submission_client_version` as the version of the client submitting the listen. Its documentation also distinguishes a recording ID submitted by the client from an ID the ListenBrainz server later resolves by matching metadata. That distinction matters here: this app's version table measures the submitted value, and its “usable” recording ID test checks UUID syntax; it does not verify that the ID exists in MusicBrainz or that it identifies the correct recording.

**Sources:**

- [Scrobbling](https://navidrome.org/docs/usage/scrobbling/), Navidrome documentation: explains setup for ListenBrainz scrobbling.
- [Navidrome releases](https://github.com/navidrome/navidrome/releases), Navidrome's official GitHub project: lists versioned releases and their changes, which Sam can compare with a suspected version-specific problem.
- [JSON Documentation](https://listenbrainz.readthedocs.io/en/latest/users/json.html), ListenBrainz documentation: defines `submission_client_version` as the client version and explains the difference between client-submitted MBIDs and ListenBrainz's server-side `mbid_mapping`.
- [MusicBrainz Identifier](https://musicbrainz.org/doc/MusicBrainz_Identifier), MusicBrainz: describes MBIDs as identifiers for database entities and their use to distinguish entities with the same name.

## 3. The app in use

**Live link:** The link included in Gigi's example PDF is [the team's Streamlit app](https://appapppy-mdilrzqijilc29whq52tc2.streamlit.app/). I could not open it with the available browser tool, so its current availability and exact live behavior still need confirmation.

**What Sam selects:** Choose the visible playback date range, keep or change the “Exclude classified importers” and “Minimum distinct accounts” settings, and inspect `navidrome` from the client selector. Use the version table and weekly playback evidence to identify a version or period for follow-up. Record the exact live selections here after taking the screenshot.

**Live-app screenshot:** Still needed. Save a real screenshot from the public app as `screenshots/navidrome-version.png` beside this case and embed it here. Do not use a local run or recreate the screen.

**What the app shows, according to the code:** For the selected client and date filters, the detail view reports total listens, distinct accounts, affected accounts, and recording-MBID coverage. Its version table groups observed listens by the submitted client-version string and reports version-specific metrics. It labels missing version strings as unknown and displays the known-version share. Weekly evidence groups by UTC week beginning Monday; a partially covered edge week is flagged, and unavailable weeks are gaps rather than measured zeroes. These are observations in the selected ListenBrainz data and filters, not counts of all Navidrome users or proof of a software defect.

## 4. Reading the result for Sam's decision

**Does the number measure what Sam cares about?** Leyna: explain whether version-level listens without a syntactically valid recording MBID are a useful signal for deciding what to investigate. The app counts absent and populated-invalid IDs together as “without usable recording MBID”; the displayed coverage only tests UUID syntax. ListenBrainz says server-side `mbid_mapping` is a separate match result, so this is not a measure of correct identification.

**Who is in the rows, and who is not?** Leyna: name whose listens are represented in the selected data and who relevant to Sam may be missing. The app's stated limitation is that observed ListenBrainz submissions are an incomplete sample of playback history and client users. The app also reports unknown-version listens, which cannot be assigned to a named release.

**What outside the data matters to this decision?** Leyna: say what else Sam needs to check. Useful evidence to consider includes Navidrome's release notes and issues, a reproducible test using files with known MusicBrainz tags, the amount of unknown version metadata, and whether a proposed fix is practical. The app does not contain these facts.

**What could Sam wrongly conclude from it?** Leyna: identify a tempting but unsupported conclusion. For example, a higher unusable-ID rate for a version alone does not prove that version caused the gap; users' libraries, upgrade timing, missing version strings, and who submits to ListenBrainz may differ across versions. Decide which of these possibilities matters for this case and support it with what you saw.

**Code evidence:** `outreach/loader.py` groups by `client_version` when building version metrics and filters on inclusive playback dates; `outreach/data_rules.py` classifies an absent ID separately from a populated non-UUID ID; `outreach/views.py` presents both as “without usable recording MBID” and states that UUID syntax does not verify MusicBrainz existence. Add the exact selected dates, filters, screenshot values, and any check you personally ran after inspecting the live app.

## 5. The verdict: prove or break

Leyna: compare the app with Sam's alternatives in part 2. State whether Sam is better off using the version view to decide what to investigate, and what Sam must not use it to conclude. Then either show why the app is as good as possible for this decision with its available data, or write a team change request that improves the evidence without harming other users. Do not treat the app's ranking as proof of a cause or a fix.

```markdown
Change request: add only after Leyna decides what change is justified and writes the request in the team's `change-requests.md` format. Otherwise remove this box from the final memo.
```
