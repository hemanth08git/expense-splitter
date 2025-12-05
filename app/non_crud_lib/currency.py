def convert_currency(amount, rate):
    """
    Convert an amount using a given exchange rate.
    Example:
        convert_currency(10, 1.1) -> 11
    """
    try:
        return round(float(amount) * float(rate), 2)
    except (TypeError, ValueError):
        return None
