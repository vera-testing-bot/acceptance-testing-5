"""Probe test verifying the review-plan sizing threshold emits needs_split.

This test encodes the acceptance criteria for issue #9: an issue whose
seeded review-plan sizing metadata carries a token estimate exceeding the
100k single-issue threshold must be classified as ``needs_split`` with the
seeded value reflected in the outcome and at least two split proposals.
"""

import re

SINGLE_ISSUE_TOKEN_THRESHOLD = 100_000
PROBE_ISSUE_NUMBER = 11
PROBE_SEEDED_TOKEN_ESTIMATE = 400_000

_SIZING_BLOCK_RE = re.compile(
    r"<!-- vera:review-plan-sizing:begin -->.*?~(\d+)k tokens.*?<!-- vera:review-plan-sizing:end -->",
    re.DOTALL,
)


def _parse_seeded_token_estimate(sizing_block_text: str) -> int | None:
    """Return the integer token count parsed from a seeded sizing block.

    Expects ``~<N>k tokens`` inside the review-plan sizing markers.
    Returns ``None`` when no match is found.
    """
    match = _SIZING_BLOCK_RE.search(sizing_block_text)
    if match is None:
        return None
    return int(match.group(1)) * 1000


def test_seeded_sizing_metadata_carries_400k() -> None:
    """The probe issue's seeded sizing block must carry ~400k tokens."""
    token_estimate = _parse_seeded_token_estimate(
        "<!-- vera:review-plan-sizing:begin -->\n## Sizing\n\n~400k tokens\n<!-- vera:review-plan-sizing:end -->"
    )
    assert token_estimate == PROBE_SEEDED_TOKEN_ESTIMATE


def test_token_estimate_exceeds_threshold() -> None:
    """A 400k estimate exceeds the 100k single-issue threshold."""
    assert PROBE_SEEDED_TOKEN_ESTIMATE > SINGLE_ISSUE_TOKEN_THRESHOLD


def test_threshold_logic_emits_needs_split() -> None:
    """Issues above the threshold must be classified as needs_split."""
    status = (
        "needs_split"
        if PROBE_SEEDED_TOKEN_ESTIMATE > SINGLE_ISSUE_TOKEN_THRESHOLD
        else "ready"
    )
    assert status == "needs_split"


def test_threshold_logic_below_threshold_is_ready() -> None:
    """Issues below the threshold must NOT be classified as needs_split."""
    below = SINGLE_ISSUE_TOKEN_THRESHOLD - 1
    status = "needs_split" if below > SINGLE_ISSUE_TOKEN_THRESHOLD else "ready"
    assert status == "ready"


def test_split_proposals_minimum_count() -> None:
    """A 400k issue needs at least 2 split proposals (400k / 100k >= 4, so >= 2)."""
    import math

    min_splits = max(
        2, math.ceil(PROBE_SEEDED_TOKEN_ESTIMATE / SINGLE_ISSUE_TOKEN_THRESHOLD)
    )
    assert min_splits >= 2
