"""String helpers for normalizing whitespace."""


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace into single spaces and strip the ends.

    Args:
        text: The string to normalize.

    Returns:
        The normalized string with single-space-separated tokens, or an
        empty string when *text* is empty or all whitespace.
    """
    return " ".join(text.split())
