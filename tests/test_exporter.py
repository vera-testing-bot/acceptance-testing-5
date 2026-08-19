"""Tests for the streaming record exporter."""

import datetime
import decimal
import enum
import io
import json
import sys
import unittest.mock
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shard_app.exporter import (
    Exporter,
    to_json,
    to_jsonl,
)


def test_empty_records_produce_empty_output() -> None:
    assert to_jsonl([]) == ""


def test_single_record_emits_one_line() -> None:
    out = to_jsonl([{"id": 1, "name": "ada"}])
    assert out == '{"id":1,"name":"ada"}'


def test_multiple_records_are_newline_delimited() -> None:
    out = to_jsonl([{"id": 1}, {"id": 2}, {"id": 3}])
    assert out.splitlines() == ['{"id":1}', '{"id":2}', '{"id":3}']
    assert out.endswith("\n") is False


def test_unicode_is_preserved_not_escaped() -> None:
    out = to_jsonl([{"city": "Zürich", "emoji": "🤖"}])
    assert "Zürich" in out
    assert "🤖" in out
    assert "\\u" not in out


class _Color(enum.Enum):
    RED = "red"
    GREEN = "green"


@dataclass
class _Point:
    x: int
    y: int


@pytest.mark.parametrize(
    "value,expected",
    [
        (datetime.datetime(2026, 8, 19, 12, 0, 0), '"2026-08-19T12:00:00"'),
        (datetime.date(2026, 8, 19), '"2026-08-19"'),
        (datetime.time(12, 30, 0), '"12:30:00"'),
        (datetime.timedelta(hours=1, minutes=30), "5400.0"),
        (decimal.Decimal("3.14"), '"3.14"'),
        (b"hello", '"hello"'),
        (frozenset({"b", "a"}), '["a","b"]'),
        (_Color.RED, '"red"'),
        (_Point(1, 2), '{"x":1,"y":2}'),
    ],
)
def test_non_serializable_edge_cases(value: object, expected: str) -> None:
    assert to_json({"v": value}) == '{"v":' + expected + "}"


def test_unknown_type_raises_type_error() -> None:
    class Mystery:
        pass

    with pytest.raises(TypeError):
        to_json({"v": Mystery()})


def test_to_jsonl_streams_to_a_file_object() -> None:
    sink = io.StringIO()
    to_jsonl([{"i": i} for i in range(5)], file=sink)
    assert sink.getvalue().splitlines() == [
        '{"i":0}',
        '{"i":1}',
        '{"i":2}',
        '{"i":3}',
        '{"i":4}',
    ]


def test_to_jsonl_accepts_a_generator_without_materializing() -> None:
    def gen():
        for i in range(3):
            yield {"i": i}

    out = to_jsonl(gen())
    assert out.splitlines() == ['{"i":0}', '{"i":1}', '{"i":2}']


def test_to_jsonl_rejects_non_iterable() -> None:
    with pytest.raises(TypeError):
        to_jsonl(42)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_input",
    [
        "not a record",
        b"not a record",
        bytearray(b"not a record"),
        {"a": 1},
    ],
)
def test_to_jsonl_rejects_str_bytes_and_dict(bad_input: object) -> None:
    with pytest.raises(TypeError):
        to_jsonl(bad_input)  # type: ignore[arg-type]


def test_to_jsonl_rejects_stream_like_input() -> None:
    with pytest.raises(TypeError):
        to_jsonl(io.StringIO())  # type: ignore[arg-type]


def test_to_jsonl_rejects_non_positive_batch_size() -> None:
    with pytest.raises(ValueError):
        to_jsonl([], batch_size=0)
    with pytest.raises(ValueError):
        to_jsonl([], batch_size=-1)


def test_exporter_class_streams_in_batches(tmp_path) -> None:
    path = tmp_path / "out.jsonl"
    exporter = Exporter(path, batch_size=2)
    exporter.write_all({"id": i} for i in range(5))
    exporter.close()

    lines = path.read_text().splitlines()
    assert lines == ['{"id":0}', '{"id":1}', '{"id":2}', '{"id":3}', '{"id":4}']


def test_exporter_rejects_non_positive_batch_size(tmp_path) -> None:
    with pytest.raises(ValueError):
        Exporter(tmp_path / "out.jsonl", batch_size=0)
    with pytest.raises(ValueError):
        Exporter(tmp_path / "out.jsonl", batch_size=-1)


def test_exporter_works_as_a_context_manager(tmp_path) -> None:
    path = tmp_path / "out.jsonl"
    with Exporter(path, batch_size=2) as exporter:
        exporter.write_all({"id": i} for i in range(3))

    assert path.read_text().splitlines() == ['{"id":0}', '{"id":1}', '{"id":2}']


def test_exporter_accepts_a_file_like_destination() -> None:
    sink = io.StringIO()
    exporter = Exporter(sink, batch_size=2)
    exporter.write_all({"id": i} for i in range(3))
    exporter.close()
    assert sink.getvalue().splitlines() == ['{"id":0}', '{"id":1}', '{"id":2}']


def test_exporter_does_not_close_a_passed_in_handle() -> None:
    sink = io.StringIO()
    exporter = Exporter(sink)
    exporter.write_all([{"id": 1}])
    exporter.close()
    assert not sink.closed


def test_exporter_closes_owned_handle_even_when_flush_raises(tmp_path) -> None:
    class FailingHandle:
        def __init__(self) -> None:
            self.closed = False

        def write(self, data: str) -> None:
            raise OSError("disk full")

        def close(self) -> None:
            self.closed = True

    handle = FailingHandle()

    with unittest.mock.patch("builtins.open", return_value=handle):
        exporter = Exporter(tmp_path / "out.jsonl")
    exporter.write_all([{"id": 1}])
    with pytest.raises(OSError):
        exporter.close()
    assert handle.closed


def test_set_with_non_comparable_elements_is_sorted_by_str() -> None:
    out = to_json({"v": {1, "a", None}})
    parsed = json.loads(out)
    assert sorted(parsed["v"], key=str) == parsed["v"]


def test_bytearray_is_decoded_like_bytes() -> None:
    assert to_json({"v": bytearray(b"hello")}) == '{"v":"hello"}'


def test_exporter_round_trips_nested_structures() -> None:
    record = {"tags": ["a", "b"], "meta": {"owner": None, "active": True}}
    assert to_json(record) == '{"tags":["a","b"],"meta":{"owner":null,"active":true}}'
