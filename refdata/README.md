# Reference-data contract

Raw downloaded material and personal data do not enter `app/` or Git. The production-image ignore file excludes this entire directory. Only documentation, schemas and a non-personal disagreement ledger are tracked here.

`uv run python tools/fetch_data.py --oracle` retrieves the two Swiss files and the independent NASA JPL DE440s test kernel with hard-coded SHA256 checks. `--book` additionally downloads the author-hosted PVR textbook for local study. The download script refuses changed upstream bytes; investigate and explicitly version any update.

## A case to import into the web lab

The exact machine-readable contract is in the FastAPI schema at `/docs`. A case contains:

```json
{
  "fixture_id": "your-fixture-id",
  "program": "Jagannatha Hora",
  "program_version": "the actual exported version",
  "source_locator": "the real export/settings artifact location",
  "source_sha256": "the actual 64-character lowercase SHA256 of that artifact",
  "conventions": {"nodes": "mean", "dasha_year_days": 365.25},
  "input": {
    "birth": {
      "date": "1988-08-14", "time": "19:05:00",
      "latitude": 26.8467, "longitude": 80.9462,
      "timezone": "Asia/Kolkata", "confidence": "certificate"
    },
    "as_of": "2026-10-22T00:00:00Z"
  },
  "expected": [
    {"path": "chart.planets.sun.longitude", "kind": "angle_degrees", "value": "REPLACE WITH EXPORTED NUMERIC DEGREES"},
    {"path": "chart.planets.moon.nakshatra_index", "kind": "exact", "value": "REPLACE WITH EXPORTED ZERO-BASED INDEX"},
    {"path": "dasha.current.0.start", "kind": "datetime", "value": "REPLACE WITH OFFSET-AWARE EXPORTED DATETIME"}
  ]
}
```

The example is intentionally **not a valid expected-value fixture** until actual exported values and provenance are supplied. It never manufactures expected numbers. Use a screenshot of program settings and record ayanamsa, node mode, house convention, dasha year and sunrise settings. Repeat each case in the second reference program. Keep personal cases in `refdata/private/` or `refdata/imports/`, both ignored, and do not commit them.

Comparison status applies only to the fields supplied. It does not authenticate an uploaded source hash, certify omitted measures, promote a fixture to a golden set, or satisfy the two-program requirement. Final golden promotion requires reviewed provenance and coverage of the required quantities.

## Current disputes

`TRIAGE.json` retains both the publication's result and the adopted draft formula for the D27 example 23 conflict. The Mars moolatrikona table/prose disagreement is retained separately. These items require adjudication; tests do not erase them or relax tolerances.
