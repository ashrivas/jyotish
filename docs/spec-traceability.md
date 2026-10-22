# v2.1 traceability

This is a computation research increment, not completion of the specification's M1 or the full service. Scope boundaries are in the API response and UI, not only this document.

| Spec area | Implemented | Evidence / remaining gate |
| --- | --- | --- |
| B3 civil time | Pinned timezone data, DST gap/fold checks, recorded-offset overrides, actual unknown-time civil day | Unit/API cases include Indian war time and foreign DST; historical time records still need source verification |
| B3 positions and houses | Nine grahas, apparent geocentric Lahiri, whole-sign houses, true/mean nodes | 7,000 independent physical longitude comparisons pass; JHora/AstroSage outputs pending |
| B3 nakshatras/padas | Half-open integer bins; display rounding separate | Boundary and property checks pass |
| B3 all 16 vargas | One pinned sign-mapping method | 26 consistent published worked cases plus boundary tests; one conflicting D27 example quarantined; no blanket JHora validation |
| B3 Vimshottari | Three-level tree, year conventions, half-open intervals, current period at explicit epoch | Partition invariants and exact-boundary tests; external dates and continuous time-window extrema pending |
| B3 strengths | Dignity, relationships, ownership, sign aspects, isolated uchcha component | Full Shadbala/bhava bala, Vimshopaka, adopted combustion/war and functional nature remain missing |
| B3 Ashtakavarga | PAV/BAV/SAV and two reductions | Fixed totals and worked reductions checked; external full-chart reference pending |
| B3 panchang | Birthplace sunrise, tithi, nakshatra, vara, nitya yoga number and half-tithi index | No-sunrise behavior checked in input matrix; official PAC numerical checks pending |
| B3 flags | Separate geometric Manglik bases; Sade Sati status at `as_of` | No cancellation claims or ingress dates |
| B3 compatibility | Not implemented | Ten externally checked pairs required |
| B3 robustness | Angular and station events, interval fractions, no fabricated ascendant for unknown time | Stronger-than-95% stable criterion; dasha/strength certification and high-latitude ascendant analysis incomplete |
| B3a optional computations | Current planetary positions only | Vedha, daily-city factors, solar return, prashna, muhurta and rectification not implemented |
| B3b reference data | Download/hash tool, independent JPL oracle, 30-case input matrix, typed import comparator, triage ledger | Inputs are not mislabeled as golden output. External reference acquisition and normalization remain open |
| B4 corpus | Four core books cataloged with explicit edition/review gaps; three technical/cross-reference additions | No ingested, approved classical corpus. No fabricated verses or reviewer signatures |
| B4 rules | Typed technical drafts with source locators, operands, facts and fire/silent checks | Full DSL, reviewed effects/weights/activation/conflicts and scholarly agreement are pending |
| B4 dossier | Disabled | Compute and knowledge gates not passed; product API credential not configured |
| B4 rendering | Closed factual templates and schema/ID mutation checks | Full multilingual dossier renderer/verifier not implemented |
| B5 covenant | No conversational generation path | Full command/classifier/distress/refusal suite is not implemented or claimed to pass |
| B8 evals | Executable code tests, independent numerical suite, provenance-aware comparisons, all 19 suite states displayed | Most service/interpretation/human suites blocked, not disguised as passes |
| B6/B7 channels and commerce | Deliberately outside the user's first-step scope | No WhatsApp, payments, voice, user database or public hosting |

The full 19-suite ledger is defined in `app/evaluation.py`. Recorded results are in `evals/results/`; locally rerun reports are written to ignored `var/evals/`.
