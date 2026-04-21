#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""TDD tests for utils/json_manager.py — load_json, save_json, merge_json.

Run from the project root:
    python -m pytest tests/test_json_manager.py -v
"""

import json

import pytest

from utils.json_manager import load_json, merge_json, save_json


# ---------------------------------------------------------------------------
# load_json
# ---------------------------------------------------------------------------

class TestLoadJson:
    def test_loads_valid_file(self, tmp_path):
        path = tmp_path / "data.json"
        path.write_text('{"key": "value", "count": 42}', encoding="utf-8")
        result = load_json(path)
        assert result == {"key": "value", "count": 42}

    def test_loads_arabic_content(self, tmp_path):
        path = tmp_path / "ar.json"
        payload = {"name": "اختبار", "count": 1}
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        result = load_json(path)
        assert result["name"] == "اختبار"

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json")

    def test_missing_file_returns_default_when_provided(self, tmp_path):
        default = {"fallback": True}
        result = load_json(tmp_path / "nonexistent.json", default=default)
        assert result == default

    def test_missing_file_default_none_still_raises(self, tmp_path):
        """default=None (the sentinel) should NOT suppress the exception."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json", default=None)

    def test_invalid_json_raises_value_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid json!!}", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json(path)

    def test_accepts_string_path(self, tmp_path):
        path = tmp_path / "str.json"
        path.write_text('{"ok": true}', encoding="utf-8")
        result = load_json(str(path))
        assert result == {"ok": True}


# ---------------------------------------------------------------------------
# save_json
# ---------------------------------------------------------------------------

class TestSaveJson:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "out.json"
        save_json({"x": 1}, out)
        assert out.exists()

    def test_content_is_valid_json(self, tmp_path):
        out = tmp_path / "out.json"
        save_json({"a": 1, "b": [2, 3]}, out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded == {"a": 1, "b": [2, 3]}

    def test_creates_nested_parent_dirs(self, tmp_path):
        out = tmp_path / "deep" / "nested" / "file.json"
        save_json({"created": True}, out)
        assert out.exists()

    def test_arabic_content_not_escaped(self, tmp_path):
        """ensure_ascii=False — Arabic characters must not become \\uXXXX."""
        out = tmp_path / "ar.json"
        save_json({"نص": "عربي"}, out)
        raw = out.read_text(encoding="utf-8")
        assert "عربي" in raw
        assert "\\u" not in raw

    def test_pretty_printed_with_indent(self, tmp_path):
        out = tmp_path / "pretty.json"
        save_json({"k": "v"}, out, indent=2)
        raw = out.read_text(encoding="utf-8")
        assert "\n" in raw  # multi-line means indent applied

    def test_overwrite_existing_file(self, tmp_path):
        out = tmp_path / "overwrite.json"
        save_json({"v": 1}, out)
        save_json({"v": 2}, out)
        assert load_json(out)["v"] == 2

    def test_roundtrip_load_save_load(self, tmp_path):
        original = {"codes": {"A": {"seq": 1}, "B": {"seq": 2}}}
        out = tmp_path / "rt.json"
        save_json(original, out)
        result = load_json(out)
        assert result == original


# ---------------------------------------------------------------------------
# merge_json
# ---------------------------------------------------------------------------

class TestMergeJson:
    def test_simple_merge_adds_keys(self):
        base = {"a": 1}
        override = {"b": 2}
        result = merge_json(base, override)
        assert result == {"a": 1, "b": 2}

    def test_override_wins_on_conflict(self):
        base = {"key": "original"}
        override = {"key": "updated"}
        result = merge_json(base, override)
        assert result["key"] == "updated"

    def test_base_unchanged(self):
        """merge_json must not mutate the base dict."""
        base = {"x": 1}
        merge_json(base, {"x": 99})
        assert base["x"] == 1

    def test_deep_merge_nested_dicts(self):
        base = {"outer": {"a": 1, "b": 2}}
        override = {"outer": {"b": 99, "c": 3}}
        result = merge_json(base, override)
        assert result["outer"] == {"a": 1, "b": 99, "c": 3}

    def test_deep_merge_three_levels(self):
        base = {"l1": {"l2": {"l3": "deep"}}}
        override = {"l1": {"l2": {"extra": "yes"}}}
        result = merge_json(base, override)
        assert result["l1"]["l2"]["l3"] == "deep"
        assert result["l1"]["l2"]["extra"] == "yes"

    def test_non_dict_override_replaces_dict(self):
        """If override value is not a dict, it replaces even a dict base value."""
        base = {"key": {"nested": "value"}}
        override = {"key": "flat"}
        result = merge_json(base, override)
        assert result["key"] == "flat"

    def test_empty_base(self):
        result = merge_json({}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_override_returns_copy_of_base(self):
        base = {"a": 1, "b": 2}
        result = merge_json(base, {})
        assert result == base
        assert result is not base  # must be a copy

    def test_list_values_replaced_not_merged(self):
        """Lists are NOT deep-merged — override replaces the whole list."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = merge_json(base, override)
        assert result["items"] == [4, 5]
