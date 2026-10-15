# 00 Vision — Client Metadata Outreach Prioritizer

## User and decision

A MetaBrainz Foundation project lead preparing a quarterly outreach pilot needs to decide **which active ListenBrainz client maintainer to contact first** about improving submission of MusicBrainz recording identifiers (MBIDs). The tool supports a human outreach decision; it does not contact maintainers automatically.

## Why this is useful

A recording MBID identifies a specific recording more reliably than artist and track text alone. Today, a project lead would have to inspect listening-data exports, group records by the software that submitted them, distinguish active listening clients from historical importers, and manually compare results. Ranking clients only by listen volume can overvalue a few heavy users or bulk imports; ranking only by missing-ID percentage can overvalue tiny clients.

The **Client Metadata Outreach Prioritizer** makes the trade-offs visible in one Streamlit app: a ranked shortlist, a closer look at a selected client, and a comparison of potential improvement scenarios. It helps the lead select a promising pilot partner based on evidence rather than a single raw count.

## What the user cares about

- **Reach:** how many distinct accounts could benefit, not just how many listens a client submits.
- **Opportunity:** how many listens lack a recording MBID, alongside the client's current MBID coverage.
- **Relevance:** separating regular submission clients from bulk importers, and showing the observation period.
- **Transparency:** seeing how rankings and estimates were calculated, including uncertain or missing evidence.
- **Practical action:** selecting a small number of clients for further research without exposing individual user identities.

## Concrete use cases

1. **Build a pilot shortlist.** The lead selects a playback-date range, excludes bulk importers, and sets a minimum distinct-account count. The tool shows a ranked table with each client's total listens, accounts, affected accounts, missing-MBID listens, and current coverage. The lead chooses two or three maintainers to investigate.

2. **Check a candidate's data quality.** The lead selects a client from the shortlist. The tool shows its metrics, available client-version breakdown, and the assumptions behind its ranking. The lead decides whether the missing-ID opportunity is broad enough to justify contacting its maintainer.

3. **Compare competing priorities.** The lead adjusts the emphasis on affected-account reach versus missing-MBID volume and compares two candidates. The tool shows how rankings change and estimates additional MBID-tagged listens under a user-selected coverage target. The lead chooses which pilot is more attractive, understanding that the estimate is a scenario rather than a guaranteed result.

4. **Prepare for outreach.** After choosing a candidate, the lead reviews and exports a short aggregate-data briefing containing the client's metrics, selected settings, and assumptions. The lead uses it for a human review and decides whether to begin a pilot conversation.

## Boundaries

The tool analyzes observed ListenBrainz data, not the full population of client users. A missing MBID does not prove that the submitting client caused the problem. Rankings and scenario estimates are **screening aids**, not causal findings, guarantees of improvement, or automated outreach decisions. Identifiable listener-level data is never shown in the interface or exports.