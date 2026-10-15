 Project Objective

## Stakeholder decision analysis

The following separates what is known from the data, what is an analytical
hypothesis, and what must be confirmed with a real stakeholder.

### Role 1: Navidrome project lead

**Decision:** Should the next release prioritize user listening statistics or
metadata quality and MusicBrainz identifier coverage?

**What this stakeholder would care about**

- **Desired outcomes:** increase user value and retention; improve the accuracy
  and usefulness of the music library; focus the small development team on the
  highest-impact work; and preserve Navidrome's open-source maintainability.
- **Risks of the wrong decision:** spending a release cycle on statistics that
  few users use; leaving metadata errors unresolved; breaking existing library
  matching; increasing maintenance burden; or investing in a feature without
  reliable data to support it.
- **Tradeoffs:** statistics can create visible user value from existing listening
  history, while metadata improvements may be less visible but improve search,
  organization, joins, and the reliability of future statistics. A metadata
  pilot may delay a more engaging user-facing feature.
- **Constraints:** limited developer time, open-source contributors, varying
  metadata quality across clients, privacy expectations, and the fact that
  ListenBrainz behavior may not represent all Navidrome users.
- **Evidence needed:** Navidrome-specific identifier match rates; the number of
  affected users and listens; frequency and severity of metadata corrections;
  statistics feature usage; user requests; implementation effort; and evidence
  that either change improves retention or satisfaction.
- **Measures of success:** higher recording and release identifier coverage;
  fewer metadata corrections; more successful library joins; statistics-page
  adoption; positive user feedback; no material increase in sync failures or
  maintenance cost; and improved retention or engagement where measurable.

**Evidence that could change the recommendation:** strong Navidrome telemetry
showing high demand for statistics, low usage of metadata-dependent features, or
a metadata fix that is unusually expensive or technically risky would favor
statistics. Conversely, a high rate of metadata failures or failed joins and a
low-cost identifier fix would strengthen the metadata recommendation.

### Role 2: MetaBrainz Foundation maintainer

**Decision:** Which scrobbling program should MetaBrainz approach first about
sending reliable MusicBrainz identifiers?

**What this stakeholder would care about**

- **Desired outcomes:** increase the number and share of listens linked to
  MusicBrainz entities; improve downstream metadata quality; help users receive
  better music history and discovery; and use limited outreach and engineering
  resources where they produce the greatest benefit.
- **Risks of the wrong decision:** spending outreach effort on a small program;
  asking a program to change without understanding its technical constraints;
  creating invalid or low-quality identifiers; damaging a partner relationship;
  or optimizing for volume while neglecting identifier accuracy.
- **Tradeoffs:** the largest program offers the greatest possible reach, but may
  be harder to change. A smaller program may be more responsive and provide a
  faster pilot. More identifiers improve joins, but incorrect identifiers can be
  worse than missing identifiers.
- **Constraints:** partner willingness, maintainer time, API and client
  limitations, MusicBrainz matching quality, privacy and consent, and the
  non-representative nature of the public sample.
- **Evidence needed:** listens and distinct accounts by program; current
  recording, artist, and release identifier coverage; identifier validity and
  match accuracy; technical ownership; effort to implement; and willingness to
  participate in a pilot.
- **Measures of success:** increased valid identifier coverage, more unique
  listens and accounts joinable to reference metadata, fewer unresolved or
  ambiguous matches, successful partner adoption, and sustained coverage after
  the initial outreach.

**Evidence that could change the recommendation:** confirmation that a smaller
program has a willing owner and a low-effort integration could move it ahead of
the highest-volume program. Evidence that the apparent gap comes from the
ListenBrainz import process rather than the original scrobbling program would
also change the outreach target.

### Audience comparison

| Dimension | Navidrome project lead | MetaBrainz maintainer |
|---|---|---|
| Primary focus | Product value and release priority | Ecosystem-wide identifier coverage |
| Main unit of impact | Navidrome users, libraries, and sessions | Listens, accounts, and partner programs |
| Preferred evidence | Usage, satisfaction, retention, effort, and reliability | Volume, coverage, validity, reach, and partner feasibility |
| Main risk | Building the wrong product capability | Spending outreach resources on the wrong integration |
| Near-term success | Better user experience with manageable maintenance | More valid, reusable MusicBrainz-linked data |

## Facts, hypotheses, and stakeholder questions

### Sourced or computed facts

- The supplied dataset overview identifies Navidrome as an illustrative example
  of an open-source music-server stakeholder and MetaBrainz as the organization
  that publishes and maintains ListenBrainz-related data resources.
- The supplied sample contains 21,276 listens from 4,060 accounts. These figures,
  the 889 Navidrome listens, identifier coverage percentages, and program counts
  above are computed from `dataset_listenbrainz/sample/listens_20260904.csv`.
- The dataset overview states that the public data has population and coverage
  limits and should not automatically be treated as representative of all music
  listeners or all Navidrome users.

### AI-generated hypotheses to test

- Navidrome users would receive more immediate value from accurate metadata than
  from a new statistics feature.
- Recording and release identifier improvements would improve both library
  metadata and future statistics, making a metadata pilot a useful first step.
- The largest-volume reporting program is the best first outreach target for
  MetaBrainz, provided its technical owner is willing and the identifiers can be
  validated.
- A small, reversible pilot is preferable to committing an entire release cycle
  before user demand and implementation effort are known.

### Questions requiring a real stakeholder

- Which Navidrome user problems are currently most frequent: missing metadata,
  poor matching, search issues, or requests for listening statistics?
- What are Navidrome's current statistics-page usage, retention, support-ticket,
  and feature-request measures?
- How much engineering time can Navidrome and MetaBrainz allocate to a pilot, and
  what technical changes are feasible in the next release cycle?
- Which scrobbling programs have an identifiable maintainer and are willing to
  change their payloads or matching process?
- What level of identifier accuracy is acceptable, and how should ambiguous
  matches be handled?
- What privacy, consent, licensing, or API constraints limit the collection and
  use of user-level listening data?