import math
import pytest
from analytics.calculations import balls_to_overs, overs_to_balls, ratio
from database.connection import Stddev


def test_cricket_math():
    assert overs_to_balls("4.2") == 26
    assert overs_to_balls(4) == 24
    assert balls_to_overs(26) == "4.2"
    assert ratio(100, 80, 100) == 125  # Strike rate.
    assert ratio(30, 26, 6) == pytest.approx(6.923076923)  # Economy.
    assert ratio(150, 3) == 50  # Batting/bowling average.
    assert ratio(2, 3, 100) == pytest.approx(200 / 3)  # Win percentage.
    assert ratio(10, 0) is None
    s = Stddev()
    for x in [1, 2, 3, None]:
        s.step(x)
    assert s.finalize() == pytest.approx(math.sqrt(2 / 3))


@pytest.mark.parametrize("value", ["4.6", "2.33", "-1", "abc"])
def test_invalid_overs(value):
    with pytest.raises(ValueError):
        overs_to_balls(value)
