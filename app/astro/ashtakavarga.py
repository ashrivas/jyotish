"""Numeric definitions transcribed from PVR 2000 tables 19-25, pp146-149.

Columns: Sun Moon Mars Mercury Jupiter Venus Saturn Lagna. A 1 is a benefic point;
this avoids the conflicting use of 'bindu' versus 'rekha' in different traditions.
Transcription is mechanically checked by fixed classical BAV totals, not human-approved.
"""

from app.astro.constants import PLANETS

TABLES = {
    "sun": "10100010 10100010 01010001 10100011 00011000 01011101 10100110 10100010 10111010 11110011 11111011 00010101",
    "moon": "01011000 00101000 11110111 00011100 00110110 11100011 11011100 10011000 01000100 11111101 11111111 00000000",
    "mars": "00100011 00100000 11010001 00100010 10010000 11011101 00100010 00100110 00000010 10101011 11111111 00001100",
    "mercury": "00110111 01100111 00010100 01100111 10010100 11011001 00100010 01101111 10110110 01110011 11111111 10011000",
    "jupiter": "10111001 11111101 10001010 10111001 01010111 00010111 11101001 10101000 11010101 10111101 11111101 00000010",
    "venus": "01000101 01000101 01110111 01100111 01011111 00110000 00000000 11001111 01111111 00001110 11111111 11100000",
    "saturn": "10000001 10000000 01100011 10000001 00101010 01111111 10000000 10010000 00010000 10110001 11111111 00111100",
}
EXPECTED_TOTALS = dict(zip(PLANETS[:7], (48, 49, 39, 54, 56, 52, 39)))


def trikona(values: list[int]) -> list[int]:
    result = values.copy()
    for i in range(4):
        indices = (i, i + 4, i + 8)
        minimum = min(result[j] for j in indices)
        for j in indices:
            result[j] -= minimum
    return result


def ekadhipatya(values: list[int], occupied: set[int]) -> list[int]:
    out = values.copy()
    for a, b in ((0, 7), (1, 6), (2, 5), (8, 11), (9, 10)):
        if out[a] == 0 or out[b] == 0 or (a in occupied and b in occupied):
            continue
        if (a in occupied) != (b in occupied):
            empty, full = (b, a) if a in occupied else (a, b)
            # Equality leaves the empty sign unchanged in this pinned edition.
            if out[empty] < out[full]:
                out[empty] = 0
            elif out[empty] > out[full]:
                out[empty] = out[full]
        elif out[a] == out[b]:
            out[a] = out[b] = 0
        else:
            out[a] = out[b] = min(out[a], out[b])
    return out


def ashtakavarga(positions: dict, lagna: dict | None) -> dict:
    if not lagna:
        return {"status": "unavailable", "reason": "Birth time unknown; no invented lagna contribution."}
    refs = [positions[n]["sign_index"] for n in PLANETS[:7]] + [lagna["sign_index"]]
    occupied = set(refs[:7])  # Nodes and lagna do not occupy signs for this reduction.
    bav, pav, reduced = {}, {}, {}
    for planet, text in TABLES.items():
        rows = text.split()
        if len(rows) != 12 or any(len(r) != 8 for r in rows):
            raise ValueError("Malformed Ashtakavarga definition")
        if sum(int(c) for r in rows for c in r) != EXPECTED_TOTALS[planet]:
            raise ValueError(f"Ashtakavarga transcription failed fixed total: {planet}")
        matrix = [[0] * 12 for _ in range(8)]
        for h, row in enumerate(rows):
            for k, cell in enumerate(row):
                matrix[k][(refs[k] + h) % 12] = int(cell)
        values = [sum(matrix[k][s] for k in range(8)) for s in range(12)]
        pav[planet] = matrix
        bav[planet] = values
        tri = trikona(values)
        reduced[planet] = {"trikona": tri, "ekadhipatya": ekadhipatya(tri, occupied)}
    sav = [sum(bav[p][s] for p in PLANETS[:7]) for s in range(12)]
    if sum(sav) != 337:
        raise ValueError("SAV total invariant failed")
    return {
        "status": "computed",
        "bhinna": bav,
        "sarva": sav,
        "prastara": pav,
        "reductions": reduced,
        "source": "pvr-2000:12.tables19-25;12.7.1-2",
        "validation": "fixed totals checked; JHora export comparison pending",
    }
