from datetime import datetime, timedelta, timezone
import pytest
from app.astro.time import resolve, birth_window, TimeResolutionError
from app.models import BirthInput


def test_dst_gap_is_not_silently_normalized():
    with pytest.raises(TimeResolutionError, match="does not exist"):
        resolve(datetime(2024, 3, 10, 2, 30), "America/New_York")


def test_dst_overlap_requires_a_choice():
    dt = datetime(2024, 11, 3, 1, 30)
    with pytest.raises(TimeResolutionError, match="occurred twice"):
        resolve(dt, "America/New_York")
    assert resolve(dt, "America/New_York", 1) - resolve(dt, "America/New_York", 0) == timedelta(hours=1)


@pytest.mark.parametrize(
    "local,zone,expected",
    [
        (datetime(1975, 7, 4, 12), "America/New_York", datetime(1975, 7, 4, 16, tzinfo=timezone.utc)),
        (datetime(1943, 8, 15, 12), "Asia/Kolkata", datetime(1943, 8, 15, 5, 30, tzinfo=timezone.utc)),
        (datetime(1988, 8, 14, 19, 5), "Asia/Kolkata", datetime(1988, 8, 14, 13, 35, tzinfo=timezone.utc)),
        (datetime(2024, 1, 1, 12), "Australia/Sydney", datetime(2024, 1, 1, 1, tzinfo=timezone.utc)),
        (datetime(2024, 1, 1, 0, 1), "Asia/Kathmandu", datetime(2023, 12, 31, 18, 16, tzinfo=timezone.utc)),
    ],
)
def test_known_civil_time_cases(local, zone, expected):
    assert resolve(local, zone) == expected


@pytest.mark.parametrize("day,hours", [("2024-03-10", 23), ("2024-11-03", 25)])
def test_unknown_birth_time_uses_actual_local_day(day, hours):
    b = BirthInput.model_validate(
        {
            "date": day,
            "latitude": 40.7,
            "longitude": -74,
            "timezone": "America/New_York",
            "confidence": "unknown",
        }
    )
    _, a, z = birth_window(b)
    assert (z - a).total_seconds() == hours * 3600


def test_historical_record_can_override_regional_timezone():
    b = BirthInput.model_validate(
        {
            "date": "1900-01-01",
            "time": "12:00",
            "latitude": 19.07,
            "longitude": 72.87,
            "timezone": "Asia/Kolkata",
            "confidence": "exact",
            "civil_offset_seconds": 17460,
            "civil_offset_source": "Synthetic Bombay-time record",
        }
    )
    utc, _, _ = birth_window(b)
    assert utc.hour == 7 and utc.minute == 9


def test_override_requires_provenance():
    with pytest.raises(ValueError, match="record source"):
        BirthInput.model_validate(
            {
                "date": "1900-01-01",
                "time": "12:00",
                "latitude": 19,
                "longitude": 72,
                "timezone": "Asia/Kolkata",
                "civil_offset_seconds": 17460,
            }
        )


@pytest.mark.parametrize("name", ["../../etc/passwd", "/etc/passwd", "Asia/MadeUp"])
def test_bad_timezone_names(name):
    with pytest.raises(TimeResolutionError):
        resolve(datetime(2000, 1, 1), name)
