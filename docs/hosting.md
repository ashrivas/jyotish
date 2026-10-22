# Private Vercel test deployment

## Target and access

- Team: `neelimashri57` (`team_0bEot0ava1MS6SkR8jWIG3SM`).
- Project: `jyotish` (`prj_v04qdAjGprRLpEsFrh8aTyMzXQxK`). Never reuse the `college-agent` project or its configuration.
- Dashboard: https://vercel.com/neelimashri57/jyotish.
- Framework: FastAPI, Python 3.13, entrypoint `app.main:app`.
- Environment: **Preview**. Enable Vercel Authentication for previews before deployment.
- Scope: owner-only research testing. No public production service, custom domain, messaging integration, database or model credential is needed.

The separate project is connected to `ashrivas/jyotish` through the existing Vercel GitHub installation. The owner approved adding only this repository to the installation's selected-repository list. Its production branch is reserved as `release/production`, so pushes to `main` target Preview. The project's Ignored Build Step is also set to **Only build pre-production**, which skips non-preview builds during this research phase. Standard Vercel Authentication is enabled for previews. A future production release requires an explicit change to these settings and a licensing/access review; it is not part of this setup.

The source repository is https://github.com/ashrivas/jyotish. Supply the real 40-character commit through Git deployment metadata; the build requires `VERCEL_GIT_COMMIT_SHA`. The build command is declared in `pyproject.toml`, with the locked install and function settings in `vercel.json`.

## Build and runtime contract

1. `uv sync --dev --locked` installs the reviewed lockfile.
2. The hosted build downloads pinned Swiss kernels and the independent NASA/JPL oracle. Every download is SHA256-verified.
3. Code checks and the full 1,000-epoch / 7,000-comparison astronomy suite must pass; tests are never skipped for a missing oracle.
4. `data/hosted/report.json` records fresh results, source commit, kernel digests, build timestamp and the raw report digest. The report is generated during the build and is not checked into Git.
5. Runtime accepts only the report matching its deployment commit. It computes charts with the same engine and conventions as the local application. The hosting mode does not enter the numerical hash.
6. The hosted API rejects background evaluation launches. In-memory jobs are suitable only for local use; instance affinity, a writable filesystem and process survival are not assumed.

The UI's refresh button reloads existing build evidence. It never claims to launch checks. GitHub Actions remains independently accessible. Manual chart inputs and uploaded references are processed in memory, without application persistence or request-body logging. Do not enable request-body capture in hosting observability. Cloud hosting still processes these inputs on the hosting provider's infrastructure; it is not on-device computation.

`.vercelignore` excludes local runtimes, credentials, raw books, private reference cases and screenshots from the source upload. Runtime exclusions also omit the large oracle kernel, raw books and private directories. Only the small non-personal source-disagreement ledger and synthetic input matrix are required from the reference/test directories. Generated artifacts and `.vercel` linkage are ignored by Git.

## Verification before handing over a URL

- Confirm Jyotish's project ID differs from the campus project's ID and belongs to the intended shared team; inspect preview authentication configuration.
- Confirm the unauthenticated page and API are intercepted by Vercel Authentication.
- Use authenticated access for the six views and a complete chart submission, including a ±5-minute uncertainty window and unknown-time mode.
- Compare deployed chart/run hashes and unrounded planetary positions with a local calculation of the same frozen synthetic request.
- Confirm same-origin HTTPS writes work behind the platform proxy and unrelated origins are rejected.
- Inspect the report's commit, code-test count, independent comparisons and unaltered release blockers.
- Verify background eval POST returns 409 and no job starts.
- Inspect build/runtime errors. Do not disable deployment protection to make automation pass.

## Dependency licenses

Swiss Ephemeris and `pyswisseph` have AGPL/commercial licensing conditions. This private owner-only test deployment does not make a licensing choice for a future distributed or public product. No AGPL relicensing of the user's entire project and no license purchase is performed by this setup. Before inviting additional testers or opening service access, choose the applicable licensing route and fulfill its requirements. Source code is available in the linked repository; no copyrighted textbook or translation is bundled.

Primary guidance: [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [Vercel Authentication](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication), [Swiss Ephemeris licensing](https://www.astro.com/swisseph/swephinfo_e.htm).
