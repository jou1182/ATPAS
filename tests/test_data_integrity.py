#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Data-integrity tests for utils/json_manager.py.

Covers the atomic-write guarantee, corruption recovery, concurrent-style
writes, and TypedDict round-trips introduced in the hardening sprint.

Run from the project root:
    python -m pytest tests/test_data_integrity.py -v
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.json_manager import load_json, merge_json, save_json


# ---------------------------------------------------------------------------
# Atomic write safety
# ---------------------------------------------------------------------------

class TestAtomicWrite:
    """save_json must never leave the target file in a partial state."""

    def test_no_tmp_file_left_on_success(self, tmp_path: Path) -> None:
        """After a successful save, no .tmp sibling should remain."""
        target = tmp_path / "data.json"
        save_json({"ok": True}, target)
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f"Unexpected .tmp files: {tmp_files}"

    def test_no_tmp_file_left_on_failure(self, tmp_path: Path) -> None:
        """If json.dump raises, the temp file must be cleaned up."""
        target = tmp_path / "data.json"

        class Unserializable:
            pass

        with pytest.raises(TypeError):
            save_json({"bad": Unserializable()}, target)

        tmp_files = list(tmp_path.glob("*.tmp"))
        assert tmp_files == [], f".tmp not cleaned up: {tmp_files}"

    def test_original_file_unchanged_on_failure(self, tmp_path: Path) -> None:
        """A failed overwrite must not corrupt the existing file."""
        target = tmp_path / "data.json"
        original = {"version": 1, "data": "safe"}
        save_json(original, target)

        class Boom:
            pass

        with pytest.raises(TypeError):
            save_json({"data": Boom()}, target)

        # Original content intact
        assert load_json(target) == original

    def test_write_is_visible_after_rename(self, tmp_path: Path) -> None:
        """After save_json returns, the file is immediately readable."""
        target = tmp_path / "visible.json"
        payload = {"arabic": "عربي", "count": 42}
        save_json(payload, target)
        assert load_json(target) == payload

    def test_atomic_overwrite_of_existing_file(self, tmp_path: Path) -> None:
        """Overwriting an existing file produces correct content, not a mix."""
        target = tmp_path / "overwrite.json"
        save_json({"v": 1}, target)
        save_json({"v": 2}, target)
        result = load_json(target)
        assert result == {"v": 2}

    def test_parallel_writes_to_independent_files_do_not_corrupt(
        self, tmp_path: Path
    ) -> None:
        """Each thread writes to its OWN file — no shared target, no contention.

        This verifies that atomic writes work correctly for the common case:
        multiple independent save operations running concurrently, each to a
        different path (e.g. different owner spec files).
        """
        n_threads = 6
        targets   = [tmp_path / f"file_{i}.json" for i in range(n_threads)]
        errors: list[Exception] = []

        def writer(path: Path, idx: int) -> None:
            try:
                for seq in range(30):
                    save_json({"thread": idx, "seq": seq, "data": "x" * 100}, path)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [
            threading.Thread(target=writer, args=(targets[i], i))
            for i in range(n_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        # Every file must be valid JSON after all writes
        for path in targets:
            data = load_json(path)
            assert isinstance(data, dict), f"{path} not valid JSON after concurrent writes"


# ---------------------------------------------------------------------------
# Corruption detection on load
# ---------------------------------------------------------------------------

class TestLoadCorruption:
    """load_json should raise clear errors on bad files."""

    def test_truncated_json_raises_value_error(self, tmp_path: Path) -> None:
        p = tmp_path / "trunc.json"
        p.write_bytes(b'{"key": "val')  # deliberately truncated
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json(p)

    def test_empty_file_raises_value_error(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.json"
        p.write_bytes(b"")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json(p)

    def test_binary_garbage_raises_value_error(self, tmp_path: Path) -> None:
        p = tmp_path / "garbage.json"
        p.write_bytes(b"\x00\x01\x02\xff")
        with pytest.raises((ValueError, UnicodeDecodeError, OSError)):
            load_json(p)

    def test_default_returned_instead_of_fnf(self, tmp_path: Path) -> None:
        result = load_json(tmp_path / "no_file.json", default={"fallback": True})
        assert result == {"fallback": True}

    def test_no_default_raises_fnf(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "no_file.json")


# ---------------------------------------------------------------------------
# Deep merge edge cases
# ---------------------------------------------------------------------------

class TestMergeEdgeCases:
    """merge_json correctness for unusual inputs."""

    def test_merge_with_none_values(self) -> None:
        result = merge_json({"a": 1}, {"a": None})
        assert result["a"] is None

    def test_merge_preserves_list_items(self) -> None:
        """Lists are replaced, not element-merged — document this behaviour."""
        result = merge_json({"codes": ["A", "B"]}, {"codes": ["C"]})
        assert result["codes"] == ["C"]

    def test_deeply_nested_merge_five_levels(self) -> None:
        base     = {"l1": {"l2": {"l3": {"l4": {"l5": "original"}}}}}
        override = {"l1": {"l2": {"l3": {"l4": {"l5": "updated", "extra": True}}}}}
        result   = merge_json(base, override)
        assert result["l1"]["l2"]["l3"]["l4"]["l5"] == "updated"
        assert result["l1"]["l2"]["l3"]["l4"]["extra"] is True

    def test_merge_does_not_mutate_either_arg(self) -> None:
        base     = {"x": {"y": 1}}
        override = {"x": {"y": 2}}
        _        = merge_json(base, override)
        assert base["x"]["y"] == 1
        assert override["x"]["y"] == 2

    def test_merge_integer_zero_not_treated_as_falsy(self) -> None:
        result = merge_json({"n": 5}, {"n": 0})
        assert result["n"] == 0

    def test_merge_boolean_false_not_skipped(self) -> None:
        result = merge_json({"flag": True}, {"flag": False})
        assert result["flag"] is False


# ---------------------------------------------------------------------------
# Arabic content round-trip
# ---------------------------------------------------------------------------

class TestArabicRoundTrip:
    """Critical: Arabic characters must survive save → load intact."""

    def test_arabic_keys_and_values(self, tmp_path: Path) -> None:
        payload = {
            "اسم": "مشروع الصرف الصحي",
            "codes": ["001-SUR-BASE", "002-EXC-FINE"],
            "الجهة": "شركة المياه الوطنية",
        }
        p = tmp_path / "arabic.json"
        save_json(payload, p)
        result = load_json(p)
        assert result["اسم"] == "مشروع الصرف الصحي"
        assert result["الجهة"] == "شركة المياه الوطنية"

    def test_arabic_not_escaped_in_file(self, tmp_path: Path) -> None:
        """Raw Arabic bytes must be in the file, not \\uXXXX sequences."""
        p = tmp_path / "raw.json"
        save_json({"text": "عروض فنية"}, p)
        raw = p.read_text(encoding="utf-8")
        assert "عروض فنية" in raw
        assert "\\u" not in raw

    def test_mixed_arabic_english_keys(self, tmp_path: Path) -> None:
        payload = {"name_ar": "صرف صحي", "name_en": "Wastewater", "count": 64}
        p = tmp_path / "mixed.json"
        save_json(payload, p)
        assert load_json(p) == payload
