from typing import Iterable

from jreads import BLACK, WHITE


def rowLines(row: Iterable[int], tolerance: int = 0):
    """
    Yield black lines from the row.
    """
    lineStart = lastBlack = None
    whiteCount = lineLength = 0

    for offset, pixel in enumerate(row):
        if pixel == BLACK:
            lineLength += 1
            whiteCount = 0
            if lineStart is None:
                lineStart = offset
            lastBlack = offset
        else:
            assert pixel == WHITE
            whiteCount += 1

            if lastBlack is None:
                # We've never seen a black pixel.
                continue

            assert offset > lastBlack
            if lineStart is not None:
                # In a run of black pixels we've just seen a white one.
                if whiteCount > tolerance:
                    # We've seen more white pixels than we can tolerate.
                    excessWhite = offset - lastBlack - 1
                    assert excessWhite >= 0
                    yield (lineStart, lineStart + lineLength - excessWhite)
                    lineStart = lastBlack = None
                    lineLength = 0
                else:
                    # This is a white pixel, but we haven't seen too many whites
                    # yet, so we assume it's part of the current black line.
                    lineLength += 1

    if lineStart is not None:
        # Don't include trailing whites in any final result.
        yield (lineStart, lineStart + lineLength - whiteCount)
