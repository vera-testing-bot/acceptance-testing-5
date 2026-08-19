"""Seed test, so a shard repo's CI has something to run."""

from shard_app import add


def test_add() -> None:
    assert add(2, 3) == 5
