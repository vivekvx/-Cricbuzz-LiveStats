"""Independent cricket arithmetic helpers; legal balls avoid decimal-over errors."""

from decimal import Decimal, InvalidOperation


def ratio(numerator, denominator, scale=1):
    return numerator * scale / denominator if denominator else None


def overs_to_balls(overs):
    try:
        value = Decimal(str(overs))
        whole = int(value)
        remainder = (value - whole) * 10
        if value < 0 or remainder != int(remainder) or not 0 <= remainder <= 5:
            raise ValueError("Overs must use cricket notation, e.g. 4.2")
        return whole * 6 + int(remainder)
    except (InvalidOperation, TypeError, OverflowError) as exc:
        raise ValueError("Invalid overs") from exc


def balls_to_overs(balls):
    return f"{balls // 6}.{balls % 6}"
