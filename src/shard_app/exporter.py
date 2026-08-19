"""Robust, streaming record exporter.

Serializes records to JSON / JSON Lines, handling the edge cases that break a
naive ``json.dumps`` (dates, decimals, bytes, enums, sets, dataclasses) and
streaming large iterables with bounded memory via batched writes.
"""

from __future__ import annotations

import datetime
import decimal
import enum
import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TextIO

DEFAULT_BATCH_SIZE: int = 1024

__all__ = ["DEFAULT_BATCH_SIZE", "Exporter", "to_json", "to_jsonl"]


def _validate_records(records: Iterable[Any]) -> None:
    if isinstance(records, (str, bytes, bytearray)) or isinstance(records, Mapping):
        raise TypeError("expected an iterable of records, not str/bytes/bytearray/mapping")
    if hasattr(records, "read"):
        raise TypeError("expected an iterable of records, not a stream")


def _write_batch(handle: TextIO, batch: list[str]) -> None:
    handle.write("\n".join(batch) + "\n")


def _default(obj: Any) -> Any:
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    if isinstance(obj, datetime.timedelta):
        return obj.total_seconds()
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, (set, frozenset)):
        try:
            return sorted(obj)
        except TypeError:
            return sorted(obj, key=str)
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not serializable")


def _dumps(record: Any) -> str:
    return json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=_default)


def to_json(record: Any) -> str:
    """Serialize a single record to a compact JSON string."""
    return _dumps(record)


def _iter_lines(records: Iterable[Any]) -> Iterator[str]:
    for record in records:
        yield _dumps(record)


def to_jsonl(
    records: Iterable[Any],
    *,
    file: TextIO | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> str:
    """Stream ``records`` as newline-delimited JSON.

    Edge cases:
      * Empty iterable -> no output (empty string / nothing written).
      * Non-iterable input -> ``TypeError``.
      * ``str``/``bytes``/``bytearray``/mapping/stream-like input -> ``TypeError``
        (likely caller mistakes, not records).
      * ``batch_size <= 0`` -> ``ValueError``.
      * Non-JSON-native values are normalized by :func:`_default`.

    When ``file`` is given, lines are written in batches of ``batch_size`` so
    large generators are streamed with bounded memory; an empty string is
    returned. Otherwise the joined output is returned as a string.
    """
    _validate_records(records)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    it = iter(records)

    if file is not None:
        batch: list[str] = []
        for line in _iter_lines(it):
            batch.append(line)
            if len(batch) >= batch_size:
                _write_batch(file, batch)
                batch.clear()
        if batch:
            _write_batch(file, batch)
        return ""

    return "\n".join(_iter_lines(it))


class Exporter:
    """Append-only JSON Lines exporter that batches writes to a destination."""

    def __init__(
        self, destination: Path | str | TextIO, *, batch_size: int = DEFAULT_BATCH_SIZE
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self._batch_size = batch_size
        self._owns_handle = False
        if hasattr(destination, "write"):
            self._handle: TextIO = destination  # type: ignore[assignment]
        else:
            self._handle = open(destination, "a", encoding="utf-8")
            self._owns_handle = True
        self._batch: list[str] = []

    def write_all(self, records: Iterable[Any]) -> None:
        _validate_records(records)
        for line in _iter_lines(records):
            self._batch.append(line)
            if len(self._batch) >= self._batch_size:
                self._flush()

    def close(self) -> None:
        try:
            self._flush()
        finally:
            if self._owns_handle:
                self._handle.close()

    def _flush(self) -> None:
        if not self._batch:
            return
        _write_batch(self._handle, self._batch)
        self._batch.clear()

    def __enter__(self) -> Exporter:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
