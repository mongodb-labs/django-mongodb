def truncate_ms(value):
    """Truncate microseconds to milliseconds as supported by MongoDB."""
    return value.replace(microsecond=(value.microsecond // 1000) * 1000)
