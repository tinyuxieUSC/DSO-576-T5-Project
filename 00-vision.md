# Team Project Vision: Client Metadata Outreach Prioritizer

## Who is this for, and what decision does it support?

Our project is a **Client Metadata Outreach Prioritizer** for a project lead at the MetaBrainz Foundation. ListenBrainz receives listening records from different music players, apps, and scrobbling clients. Some records include a MusicBrainz recording identifier (MBID), while many do not. Missing identifiers make it harder to reliably connect listens to the correct recordings.

The tool will help a project lead decide **which client maintainers to contact first** about improving recording MBID submissions. This decision matters when planning outreach because staff and engineering time are limited. The dashboard will recommend candidates for investigation, not automatically decide which developers should be contacted.

## What will the user see and do?

We plan to build a Streamlit dashboard with three main views:

1. **Priority Table:** Rank clients using missing recording MBIDs, number of affected accounts, existing MBID coverage, and available evidence about outreach feasibility. Users can filter by playback dates, exclude bulk importers, set a minimum account count, and adjust the importance of each ranking factor.
2. **Client Detail:** Select a client to see its listening volume, MBID coverage, affected accounts, available client-version breakdown, and the factors behind its ranking.
3. **Scenario Comparison:** Compare possible outreach targets and estimate how many additional listens might contain recording MBIDs if coverage improves to a selected target. These estimates will be labeled as scenarios, not guaranteed outcomes.

For example, a project lead could exclude historical import tools, focus on clients with at least 100 observed accounts, and give more weight to account reach than total listening volume. After comparing the leading candidates, the lead could export a short summary to guide a conversation with a client maintainer.

## Why is this useful?

Today, comparing clients can require separate queries, manual checks, and research into the software behind each submission. Simply choosing the client with the most missing IDs may be misleading: a bulk importer or a few highly active accounts could dominate the counts. Choosing only the lowest coverage percentage could also put very small clients at the top.

Our dashboard will bring the evidence together and make the tradeoffs visible. It will help the user identify clients where better metadata could benefit many listens and accounts, while still considering whether outreach seems practical.

## What data will we use?

We will use the public ListenBrainz listening-history dumps and the supplied metadata sample. Useful fields include listening timestamps, account identifiers, submission client names and versions, and recording MBIDs. With pandas, we can calculate listening counts, distinct affected accounts, missing-ID rates, and coverage by client. We may supplement this with manually verified public repository information to assess whether a client has an identifiable maintainer or contribution path.

The data does **not** tell us why an MBID is missing, whether a maintainer will respond, or the actual engineering effort required. We will therefore show unknown information clearly and avoid presenting the ranking as proof that any client caused the problem.

## What does success look like?

A successful prototype will let a project lead move from raw listening records to a clear shortlist of outreach candidates, understand why each client ranks where it does, compare at least two candidates, and explain the recommendation using visible evidence. We will use aggregated account counts rather than exposing individual user handles. The initial version can use the provided sample and a daily dump, with the possibility of expanding to multiple days to make the ranking more stable.

Our goal is a practical, transparent decision-support tool—not another general music listening dashboard.
