"""Tests for the normalize_whitespace string helper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from text_utils import normalize_whitespace


def test_normalize_collapses_internal_whitespace() -> None:
    assert normalize_whitespace("  a   b  ") == "a b"


def test_normalize_empty_string() -> None:
    assert normalize_whitespace("") == ""


def test_normalize_single_word() -> None:
    assert normalize_whitespace("   hello   ") == "hello"


def test_normalize_preserves_single_spaces() -> None:
    assert normalize_whitespace("a b c") == "a b c"


def test_normalize_handles_tabs_and_newlines() -> None:
    assert normalize_whitespace("a\t\n b\n\nc") == "a b c"
