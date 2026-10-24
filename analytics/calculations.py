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


def provider_overs_display(value):
    """Canonicalize the provider's observed .6 over-end notation."""
    try:
        number = Decimal(str(value))
        whole = int(number)
        part = (number - whole) * 10
        if number < 0 or part != int(part) or not 0 <= part <= 6:
            return str(value)
        return balls_to_overs(whole * 6 + int(part))
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        return str(value)
