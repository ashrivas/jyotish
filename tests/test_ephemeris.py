from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import pytest
from app.astro.ephemeris import snapshot, kernel_manifest, body_position, context
from app.astro.engine import compute
from app.astro.angles import separation
from app.models import ChartRequest, Conventions
from tools.dual_engine import compare


def test_independent_jpl_oracle_at_extreme_and_modern_epochs():
    # Missing oracle files fail this suite; they are never marked as passing/skipped.
    for year in (1900, 1943, 1975, 2000, 2025, 2099):
        result = compare(datetime(year, 1, 1, 12, tzinfo=timezone.utc))
        assert max(result.values()) < 1.0


def test_rahu_ketu_exactly_opposed_and_whole_sign_houses(chart_request):
    result = compute(chart_request)
    planets, lagna = result["chart"]["planets"], result["chart"]["lagna"]
    assert separation(planets["rahu"]["longitude"], planets["ketu"]["longitude"]) == pytest.approx(180)
    assert all(p["house"] == (p["sign_index"] - lagna["sign_index"]) % 12 + 1 for p in planets.values())


def test_request_hash_is_reproducible_and_as_of_is_separate(request_data):
    a = compute(ChartRequest.model_validate(request_data))
    b = compute(ChartRequest.model_validate(request_data))
    assert a == b
    request_data["as_of"] = "2027-10-22T00:00:00Z"
    c = compute(ChartRequest.model_validate(request_data))
    assert a["chart_hash"] == c["chart_hash"]
    assert a["run_hash"] != c["run_hash"]


def test_concurrent_node_modes_do_not_contaminate_each_other():
    instant = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)

    def run(mode):
        return snapshot(instant, 26.8, 80.9, Conventions(nodes=mode))["planets"]["rahu"]["longitude"]

    expected = {mode: run(mode) for mode in ("true", "mean")}
    modes = ["mean", "true"] * 20
    with ThreadPoolExecutor(8) as pool:
        result = list(pool.map(run, modes))
    assert result == [expected[m] for m in modes]
    assert abs(expected["mean"] - expected["true"]) > 0.1


def test_unexpected_fallback_is_rejected(monkeypatch):
    import swisseph as swe

    with context(Conventions()):
        monkeypatch.setattr(swe, "calc", lambda *a: ((0,) * 6, swe.FLG_MOSEPH))
        with pytest.raises(ValueError, match="fallback"):
            body_position(2451545, swe.SUN)
