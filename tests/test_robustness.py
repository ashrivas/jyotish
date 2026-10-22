from datetime import datetime, timedelta, timezone
from app.astro.robustness import angular_events, station_events
from app.astro.engine import compute
from app.models import ChartRequest


def test_boundary_finder_catches_short_lived_state_between_four_minute_samples():
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    fn = lambda t: (29.9 + (t - start).total_seconds() * 0.01) % 360
    events = angular_events(fn, start, start + timedelta(minutes=4))
    # Sign crossing at 10 seconds, much shorter than a four-minute sample interval.
    assert any(abs((event - start).total_seconds() - 10) < 0.02 for event in events)


def test_retrograde_boundary_and_circle_wrap():
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    fn = lambda t: (0.1 - (t - start).total_seconds() * 0.01) % 360
    events = angular_events(fn, start, start + timedelta(seconds=30))
    assert any(abs((event - start).total_seconds() - 10) < 0.02 for event in events)


def test_station_partition_catches_a_boundary_crossed_twice_between_scan_endpoints():
    start = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # The endpoints are both below 30 degrees. Around the station it briefly crosses 30 twice.
    angle = lambda t: 30.01 - 0.001 * ((t - start).total_seconds() - 10) ** 2
    speed = lambda t: -0.002 * ((t - start).total_seconds() - 10)
    end = start + timedelta(seconds=20)
    stations = station_events(speed, start, end)
    assert len(stations) == 1
    cuts = [start, *stations, end]
    events = [e for a, z in zip(cuts, cuts[1:]) for e in angular_events(angle, a, z)]
    # The two 30-degree crossings have the analytical solutions 10 +/- sqrt(10).
    for expected in (10 - 10**0.5, 10 + 10**0.5):
        assert any(abs((e - start).total_seconds() - expected) < 0.02 for e in events)


def test_nominal_stable_facts_have_single_alternative(chart_request):
    out = compute(chart_request)
    for fact in out["robustness"]["facts"].values():
        if fact["stability"] == "stable":
            assert fact["nominal_duration_fraction"] == 1
            assert len(fact["alternatives"]) == 1
    assert out["dasha"]["uncertainty"]["status"] == "not_certified"


def test_unknown_time_emits_no_ascendant_or_lagna_based_av(request_data):
    request_data["birth"].update(time=None, confidence="unknown")
    out = compute(ChartRequest.model_validate(request_data))
    assert out["chart"]["lagna"] is None
    assert out["chart"]["house_basis"] == "moon"
    assert out["ashtakavarga"]["status"] == "unavailable"
    assert all(not k.startswith("lagna.") for k in out["robustness"]["facts"])
