"""Seed test, so a shard repo's CI has something to run."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shard_app import add, subtract


def test_add() -> None:
    assert add(2, 3) == 5


def test_subtract() -> None:
    assert subtract(5, 3) == 2
