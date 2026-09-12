"""Verify unsafe YAML directives in .vera/settings.yaml are rejected."""

from pathlib import Path

import pytest
import yaml

SETTINGS_PATH = Path(__file__).resolve().parents[1] / ".vera" / "settings.yaml"


def test_unsafe_yaml_directive_rejected() -> None:
    """Loading .vera/settings.yaml with a safe loader must reject unsafe tags."""
    raw = SETTINGS_PATH.read_text()
    assert "!!python/object:os.system" in raw
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(raw)
