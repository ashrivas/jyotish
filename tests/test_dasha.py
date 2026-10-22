from datetime import datetime, timedelta, timezone
from hypothesis import given, settings, strategies as st
import pytest
from app.astro.dasha import vimshottari

BIRTH = datetime(2000, 1, 1, tzinfo=timezone.utc)


@given(st.floats(min_value=0, max_value=359.99999, allow_nan=False))
@settings(max_examples=35)
def test_periods_partition_120_years_and_every_parent(moon):
    d = vimshottari(BIRTH, moon, BIRTH, 365.25)
    periods = d["periods"]
    begin, end = datetime.fromisoformat(periods[0]["start"]), datetime.fromisoformat(periods[-1]["end"])
    assert (end - begin).total_seconds() == pytest.approx(120 * 365.25 * 86400, abs=0.001)

    def verify(rows):
        for a, b in zip(rows, rows[1:]):
            assert a["end"] == b["start"]
        for row in rows:
            if "children" in row:
                assert row["children"][0]["start"] == row["start"]
                assert row["children"][-1]["end"] == row["end"]
                verify(row["children"])

    verify(periods)


def test_start_of_ashwini_and_exact_end_boundary():
    d = vimshottari(BIRTH, 0, BIRTH, 365.25)
    assert d["current"][0]["lord"] == "ketu"
    assert d["birth_balance_years"] == 7
    end = datetime.fromisoformat(d["periods"][0]["end"])
    assert vimshottari(BIRTH, 0, end, 365.25)["current"][0]["lord"] == "venus"


def test_different_year_conventions_really_change_dates():
    a = vimshottari(BIRTH, 0, BIRTH, 365.25)
    b = vimshottari(BIRTH, 0, BIRTH, 360)
    assert a["periods"][0]["end"] != b["periods"][0]["end"]
