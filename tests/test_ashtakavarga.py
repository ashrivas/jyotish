from hypothesis import given, strategies as st
from app.astro.ashtakavarga import ashtakavarga, trikona, ekadhipatya
from app.astro.constants import PLANETS


@given(st.lists(st.integers(0, 11), min_size=8, max_size=8))
def test_ashtakavarga_totals_independent_of_planet_placements(signs):
    planets = {n: {"sign_index": signs[i]} for i, n in enumerate(PLANETS[:7])}
    av = ashtakavarga(planets, {"sign_index": signs[7]})
    assert [sum(av["bhinna"][n]) for n in PLANETS[:7]] == [48, 49, 39, 54, 56, 52, 39]
    assert sum(av["sarva"]) == 337
    assert all(0 <= v <= 8 for row in av["bhinna"].values() for v in row)


def test_published_trikona_example_40():
    assert trikona([7, 4, 7, 4, 4, 3, 4, 4, 4, 3, 6, 4]) == [3, 1, 3, 0, 0, 0, 0, 0, 0, 0, 2, 0]


def test_coowned_reduction_example_42():
    for occupied, a, b in [({1, 6}, 4, 2), ({1}, 4, 0), ({6}, 2, 2), (set(), 2, 2)]:
        values = [0] * 12
        values[1], values[6] = 4, 2
        out = ekadhipatya(values, occupied)
        assert (out[1], out[6]) == (a, b)
    values = [0] * 12
    values[1] = values[6] = 2
    assert ekadhipatya(values, set())[1] == ekadhipatya(values, set())[6] == 0


def test_unknown_time_does_not_invent_lagna_points():
    assert ashtakavarga({}, None)["status"] == "unavailable"
