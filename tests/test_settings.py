"""Tests verifying that settings defaults apply cleanly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shard_app.settings import Settings, load


def test_load_with_no_overrides_returns_defaults() -> None:
    settings = load()
    assert isinstance(settings, Settings)
    assert settings.debug is False
    assert settings.max_retries == 3
    assert settings.timeout == 30.0


def test_defaults_classmethod_matches_load() -> None:
    assert load() == Settings.defaults()


def test_load_with_overrides_applies_cleanly() -> None:
    settings = load({"debug": True, "max_retries": 5})
    assert settings.debug is True
    assert settings.max_retries == 5
    assert settings.timeout == 30.0


def test_load_unknown_keys_are_ignored() -> None:
    settings = load({"unknown_key": "ignored"})
    assert settings == Settings.defaults()


def test_load_does_not_raise_on_empty_dict() -> None:
    settings = load({})
    assert settings == Settings.defaults()
