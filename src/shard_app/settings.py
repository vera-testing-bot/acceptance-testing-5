"""Application settings with documented defaults."""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Settings:
    """Container for application settings.

    Defaults are chosen so the app runs out-of-the-box with no configuration.
    """

    debug: bool = False
    max_retries: int = 3
    timeout: float = 30.0

    @classmethod
    def defaults(cls) -> Settings:
        """Return a Settings instance populated with the documented defaults."""
        return cls()


def load(overrides: dict | None = None) -> Settings:
    """Return settings with ``overrides`` applied on top of the defaults.

    Unknown keys in ``overrides`` are ignored so a stale config does not
    prevent the app from starting cleanly.
    """
    valid_names = {f.name for f in fields(Settings)}
    cleaned = {k: v for k, v in (overrides or {}).items() if k in valid_names}
    return Settings(**cleaned)
