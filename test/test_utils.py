from jreads import BLACK, WHITE
from jreads.utils import rowLines


def check(expected: tuple[tuple[int, int]], row: str, tolerance: int = 0):
    assert expected == tuple(
        rowLines((BLACK if s == "B" else WHITE for s in row), tolerance)
    )


class TestZeroTolerance:
    def testEmptyRow(self):
        check((), "")

    def testWhiteRow(self):
        check((), "WWW")

    def testNonEmptyRow(self):
        check(((0, 3),), "BBB")

    def test_0_BBW(self):
        check(((0, 2),), "BBW")

    def test_0_BBWW(self):
        check(((0, 2),), "BBWW")

    def test_0_BBWBB(self):
        check(((0, 2), (3, 5)), "BBWBB")

    def test_0_WBBWBB(self):
        check(((1, 3), (4, 6)), "WBBWBB")

    def test_0_WBBWBBW(self):
        check(((1, 3), (4, 6)), "WBBWBBW")

    def test_0_WBBWWBBBWWBBW(self):
        check(((1, 3), (5, 8), (10, 12)), "WBBWWBBBWWBBW")

    def test_0_Long(self):
        check(((5, 6), (63, 66)), "WWWWWB" + "W" * 57 + "BBB" + "W" * 34)


class TestTolerance:
    def test_1_BBWBB(self):
        check(((0, 5),), "BBWBB", 1)

    def test_1_BBWWBB(self):
        check(((0, 2), (4, 6)), "BBWWBB", 1)

    def test_1_BBWWBBW(self):
        check(((0, 2), (4, 6)), "BBWWBBW", 1)

    def test_1_BBWWBBWB(self):
        check(((0, 2), (4, 8)), "BBWWBBWB", 1)

    def test_1_BBWWWBB(self):
        check(((0, 2), (5, 7)), "BBWWWBB", 1)

    def test_1_WBBWWBBBWWBBW(self):
        check(((1, 3), (5, 8), (10, 12)), "WBBWWBBBWWBBW", 1)

    def test_2_WBBWWBBBWWBBW(self):
        check(((1, 12),), "WBBWWBBBWWBBW", 2)

    def test_2_WBBWWWBBBWWBBW(self):
        check(((1, 3), (6, 13)), "WBBWWWBBBWWBBW", 2)

    def test_5_WWWWWB(self):
        check(((5, 6),), "WWWWWB", 5)

    def test_5_BWWWWWB(self):
        check(((0, 7),), "BWWWWWB", 5)

    def test_1_Long(self):
        check(((5, 6), (63, 66)), "WWWWWB" + "W" * 57 + "BBB" + "W" * 34, 1)
