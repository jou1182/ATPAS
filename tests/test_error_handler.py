#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for engine/error_handler.py.

Tests cover: arabic_message, format_user_error, safe_call.

Run from the project root:
    python -m pytest tests/test_error_handler.py -v
"""

from __future__ import annotations

import pytest

from engine.error_handler import arabic_message, format_user_error, safe_call


# ---------------------------------------------------------------------------
# arabic_message
# ---------------------------------------------------------------------------

class TestArabicMessage:
    def test_file_not_found(self) -> None:
        msg = arabic_message(FileNotFoundError("path/to/missing.json"))
        assert "موجود" in msg or "ملف" in msg

    def test_value_error(self) -> None:
        msg = arabic_message(ValueError("bad input"))
        assert msg  # non-empty

    def test_permission_error(self) -> None:
        msg = arabic_message(PermissionError("denied"))
        assert "صلاحية" in msg or "وصول" in msg

    def test_unknown_error_type_returns_default(self) -> None:
        class WeirdError(Exception): pass
        msg = arabic_message(WeirdError("oops"))
        assert msg  # default fallback

    def test_os_error(self) -> None:
        msg = arabic_message(OSError("disk full"))
        assert "ملفات" in msg or "نظام" in msg

    def test_memory_error(self) -> None:
        msg = arabic_message(MemoryError())
        assert "ذاكرة" in msg or "كافية" in msg


# ---------------------------------------------------------------------------
# format_user_error
# ---------------------------------------------------------------------------

class TestFormatUserError:
    def test_includes_arabic_label(self) -> None:
        full = format_user_error(FileNotFoundError("missing.json"))
        assert "موجود" in full or "ملف" in full

    def test_includes_context(self) -> None:
        full = format_user_error(ValueError("bad"), context="تحميل السجل")
        assert "تحميل السجل" in full

    def test_no_context_still_valid(self) -> None:
        full = format_user_error(KeyError("field"))
        assert full  # non-empty

    def test_includes_exception_type(self) -> None:
        full = format_user_error(RuntimeError("oops"))
        assert "RuntimeError" in full

    def test_includes_hint_for_file_not_found(self) -> None:
        full = format_user_error(FileNotFoundError("x"))
        assert "💡" in full or "التوصية" in full

    def test_includes_hint_for_permission_error(self) -> None:
        full = format_user_error(PermissionError("denied"))
        assert "Word" in full or "أغلق" in full or "💡" in full

    def test_unicode_decode_error_has_hint(self) -> None:
        exc = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        full = format_user_error(exc)
        assert "UTF-8" in full or "ترميز" in full or "💡" in full


# ---------------------------------------------------------------------------
# safe_call
# ---------------------------------------------------------------------------

class TestSafeCall:
    def test_success_returns_true_and_result(self) -> None:
        success, result, err = safe_call(lambda: 42)
        assert success is True
        assert result == 42
        assert err is None

    def test_failure_returns_false_and_message(self) -> None:
        def boom():
            raise FileNotFoundError("missing.json")

        success, result, err = safe_call(boom)
        assert success is False
        assert result is None
        assert err is not None
        assert "موجود" in err or "ملف" in err

    def test_context_appears_in_error_message(self) -> None:
        def boom():
            raise OSError("disk full")

        success, _, err = safe_call(boom, context="حفظ الملف")
        assert "حفظ الملف" in (err or "")

    def test_args_forwarded_to_func(self) -> None:
        success, result, _ = safe_call(lambda x, y: x + y, 3, 4)
        assert success and result == 7

    def test_kwargs_forwarded_to_func(self) -> None:
        success, result, _ = safe_call(lambda *, n: n * 2, n=5)
        assert success and result == 10

    def test_unexpected_exception_caught(self) -> None:
        def crash():
            raise RecursionError("too deep")

        success, _, err = safe_call(crash)
        assert success is False
        assert err is not None
