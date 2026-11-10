# Client Metadata Outreach Prioritizer

A screening tool for a MetaBrainz outreach coordinator deciding which ListenBrainz client maintainers to investigate for a recording-identifier improvement pilot. It compares observed account reach, submitted-ID gaps, client versions, and hypothetical coverage scenarios. A ranking helps organize research; it does not establish client causation, a feasible intervention, or likely future gains.

## Open the app

**[Public live app](https://appapppy-mdilrzqijilc29whq52tc2.streamlit.app/)** — no sign-in required. Deployed from this repository's `case-live-evidence` branch, entry point `streamlit_app.py`. Keep this deployment available through December 16, 2026.

Start with the shortlist, inspect a client, compare two or three candidates, and download an aggregate evidence briefing. Approximate scenario additions, achieved coverage, and minimum additions to reach the selected target are separately labeled. The complete comparison export retains every selected candidate; the individual-client briefing remains available.

## Submission status

**Demo video: teammate-provided link pending.** Add the unlisted YouTube link here when the teammate supplies it, and verify it opens without sign-in. The team member is handling the video separately.

**Validation:** `validation.pdf` is in the repository root, with four sections: Design, Cases, Numbers, Tests. Section 2 includes all five supplied cases: Nora, Morgan, Alex, Ana, and Rachel. The team should confirm author/case ownership and review the source cases and conclusions. The demo video link is still required before the final hand-in.

## Data used by the live app

The live app uses all **21,276 events in the course's uniform random listens sample**, not the entire raw daily dump or the full ListenBrainz population. It retains the five fields required by this app, removes user names and unused columns, and consistently replaces positive account numbers with local surrogate integers. Event counts, timestamps, client/version labels, recording IDs, and equality-based reach counts are preserved. Pseudonymization is not a claim of anonymity.

The sample can change every count, proportion, eligibility threshold result and ranking relative to full data. Its playback dates span 2005-02-13 through 2026-09-03; that does not make it a complete playback history. A submission-day dump includes historical imports. Classified importers are excluded by default; unclassified clients remain unverified. Recording-MBID coverage checks UUID syntax, not existence or correct recording identity. Account counts across clients are not additive.

Source and transformation details: [`outreach-app/demo-input/README.md`](outreach-app/demo-input/README.md). The portable sample is under 1 MB; no raw archives, external dataset folder, database account or service secret is needed. Private prepared files and a local HMAC secret are generated on first startup and are not included in the ZIP.

## Run on a laptop

Install [uv](https://docs.astral.sh/uv/getting-started/installation/). From this repository's top folder, on macOS Terminal or Windows PowerShell:

```text
uv sync --locked
uv run streamlit run streamlit_app.py
```

Open the local address printed in the terminal. The first startup prepares the bundled sample. Stop with Ctrl+C. The original advanced entry point remains in `outreach-app/app.py`; use the root entry point above for the portable sample and public deployment.

## Reproduce the validation

From the repository root:

```text
uv run python scripts/validate_mvp.py
uv run python scripts/check_case.py
cd outreach-app
uv run python -m pytest -q
```

The independent numerical audit writes `evidence/mvp-numbers.json`; the case check writes `cases/tinyu/calculation-evidence.json`. The test suite uses small exact fixtures and the bundled sample. The full-mode integration test is skipped unless a separately prepared full dataset is present; full mode is not the public deployment.

## Team and individual case

- Tinyu Xie — [case PDF](cases/tinyu/tinyu-case-nora-pilot.pdf), [final memo](cases/tinyu/nora-pilot-final.md), and [verification notes](cases/tinyu/submission-check.md).
- [Morgan / Pano version support](cases/submitted/leyna-pano-version-support.pdf) — Leyna.
- [Alex / Navidrome version priority](cases/submitted/zhongze-navidrome-versions.pdf) — Zhongze.
- [Ana / diagnostic review](cases/submitted/gigi-diagnostic-review.pdf) — Gigi.
- [Rachel / unknown client eligibility](cases/submitted/rachel-unknown-client.pdf) — supplied case; author not labeled in the PDF.

The historical case records findings before the MVP fixes. The validation documents the subsequent fixes and their new live evidence. `change-requests.md` retains the original findings and resolution status. No outreach message is sent by this app.
