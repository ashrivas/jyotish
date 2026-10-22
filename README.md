# Jyoti Accuracy Lab

A web workbench for testing the computational core of Jyoti locally or in a protected Vercel preview. Python 3.13, FastAPI, Pydantic, Swiss Ephemeris and a buildless browser UI. **This is an incomplete research build, not a certified astrologer or a completed M1.** No public service or messaging integration is configured.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/ashrivas/jyotish.git
cd jyotish
uv sync --dev --locked
uv run python tools/fetch_data.py --oracle
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The engine needs no LLM key. Binding to loopback keeps this development server on your computer. Do not expose this research server to the internet.

## Private hosted testing

The hosting configuration targets a **separate Vercel project named `jyotish`**, under the existing team. Use a **Preview** deployment with Vercel Authentication enabled for previews. This does not require changes to any other project or a database. Do not deploy an unprotected production URL; the current authorization is private testing only.

Vercel installs the locked Python 3.13 dependencies and runs `tools/build_hosted.py`. The build downloads and verifies the Swiss and independent JPL files, runs the full code suite and 7,000 independent comparisons, and fails if either suite fails. It bundles a fresh synthetic report bound to `VERCEL_GIT_COMMIT_SHA`. The page shows its tested commit and a source link. A missing report or a report from a different commit is not displayed as a pass.

Hosted **Evaluations → Refresh deployment report** reads this build's report; it does not start another run. New checks run on the next build and in [GitHub Actions](https://github.com/ashrivas/jyotish/actions/workflows/accuracy.yml). The local evaluation runner remains available on your own computer. Reference JSON comparison, manual scenarios, uncertainty inspection and exports work in both modes.

Deployment protection must be verified with an unauthenticated request, then chart submission and all six views must be checked through authenticated access. See [the hosting runbook](docs/hosting.md). Configuration being present does not mean the project has been created or deployed.

## What works

- Apparent geocentric sidereal positions for the nine grahas, Lahiri ayanamsa, whole-sign houses, nakshatras and padas.
- All 16 Parashari varga **sign mappings**, pinned to the specific PVR chapter 6 method. D30 is nonuniform; D60 is sign-relative in that reference. Alternative school conventions are not mixed together.
- Three-level Vimshottari periods, configurable year length, explicit UTC boundaries and a frozen `as_of` epoch.
- Dignity, compound friendship, house ownership, sign-based full graha aspects and the isolated uchcha-bala component. **These do not stand in for full Shadbala.**
- Prastara/Bhinna/Sarva Ashtakavarga and trinal/co-owned reductions; benefic-point notation is explicit.
- Panchang at birthplace sunrise, current planetary transits, and geometric Manglik/Sade-Sati indicators. Cancellation rules and transit ingress dates are not implemented.
- Birth-time uncertainty partitioned at angular crossings and planetary stations. Stable requires unanimity; the spec's 95% value is retained only as a separate diagnostic. Fractions describe elapsed time, not calibrated belief.
- Historical timezone/DST validation, sourced recorded-offset overrides in seconds, unknown-time Moon-chart mode, and no invented high-latitude sunrise.
- Source registry, typed technical-rule drafts, closed factual rendering, reference import/compare, raw JSON exports and a 19-suite readiness ledger.

The UI has Chart, Time uncertainty, Evidence, Evaluations, Sources and JSON views. Chart inputs are handled in memory, never written to the application log or database. Exporting birth details is an explicit browser action. Evaluation reports contain synthetic tests only. No analytics or third-party scripts are loaded.

## 60-second manual verification

1. Keep the default Lucknow example and press **Compute & inspect**. Inspect the resolved UTC, Moon in Leo and D1; switch to D9 and D60.
2. Open **Time uncertainty**. The higher varga/ascendant classifications change within the ±5-minute window even when the Moon sign is stable.
3. Open **Evidence**. Observe source-linked technical configurations and zero approved predictive rules.
4. Open **Evaluations** and run the checks. The independent astronomy suite can pass while golden-reference and expert gates remain blocked.
5. Select **Moon-Chart-Unknown**, recompute, and verify that no ascendant or lagna-dependent Ashtakavarga is fabricated.

## Tests and independent oracle

```bash
uv run python -m pytest -q
uv run python tools/run_evals.py
```

The second command runs the code tests and 1,000 seeded epochs × seven physical grahas against **Skyfield + JPL DE440s**, using the same physical TT epoch and apparent tropical frame. The initial baseline passed **133 code tests**. The astronomy limit is 1 arcsecond; the first recorded maximum was approximately **0.02759 arcseconds** across 7,000 comparisons. This checks physical longitudes, not nodes, lagna, sidereal conventions, dashas or predictions. The immutable numerical report is in `evals/results/`.

The 30-case matrix is an executable set of **input scenarios**, not 30 validated golden charts. No expected values are generated by Jyoti and relabeled as an external oracle. Missing oracle files fail numerical tests; they do not become skipped passes.

## External references

See [the reference-data contract](refdata/README.md). Import a source-recorded JSON case in the Evaluations tab or use `POST /api/compare`. Each case must freeze the inputs and conventions, identify the program/version and source artifact, and supply expected fields. Angular comparison uses 1 arcminute, dasha datetimes 1 day, panchang times 1 minute and discrete values exact. Callers cannot increase tolerances. A successful partial comparison never certifies a whole chart.

## Source shelf

The core four from the specification remain **Brihat Parashara Hora Shastra, Brihat Jataka, Saravali and Phaladeepika**. The catalog adds **Jataka Parijata** as a candidate cross-reference, **Graha and Bhava Balas** for strength worked examples, and the author-hosted **Vedic Astrology: An Integrated Approach** for computational checks. The [ACVA reading list](https://acvaonline.org/acva-recommended-reading/) and [author's download page](https://www.vedicastrologer.org/articles/astro_books.htm) support this selection.

These are respected traditional/computational references, not evidence of predictive validity. The registry is not an ingested corpus. No modern translation or textbook is redistributed. A printed edition, verse variants, use rights, proofreads and reviewer attestations are required before a classical rule can become approved. `refdata/TRIAGE.json` preserves a D27 arithmetic conflict and a Mars dignity inconsistency found in the consulted textbook.

## Remaining accuracy gates

**Not yet implemented:** full Shadbala/bhava bala, Vimshopaka bala, adopted combustion/war rules, functional-nature tables, guna milan, transit vedha/ingress search, annual/prashna/muhurta calculations, rectification and the reviewed interpretive corpus/dossier/verifier. Dasha uncertainty currently exposes only endpoint scenarios, explicitly not certified extrema.

The assistant's own model session is not a product API credential. No provider credential was present in this checkout. A live LLM path is intentionally not enabled before the computation and knowledge gates described by the spec. `claude-opus-5-5` is retained as the preferred future model; model/provider changes will be versioned and evaluated. Technical configuration checks are not forecasts.

See [spec traceability](docs/spec-traceability.md) and [architecture decisions](docs/architecture.md) for the exact implemented/deferred boundary.

## Data and licensing

Swiss `.se1` files and JPL kernels download from official maintainer/NASA sources and are checksum-verified. A missing or substituted ephemeris fails closed. Raw references, textbooks, imports, personal cases, runtimes and generated local reports are excluded from Git and the production image. `--book` downloads the author-hosted textbook into ignored local reference storage for study.

This phase is development and access-controlled testing by the project owner. Before opening access to other users or distributing a service, resolve the Swiss Ephemeris and Python binding licensing requirements and the rights for the selected textual editions. There are no payment or WhatsApp steps in this repo.
