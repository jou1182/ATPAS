#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the v3.2 global-readiness utility modules.

Covers: utils.app_version, utils.company_profile, utils.i18n,
utils.update_checker, and the multi-column engine.boq_importer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── utils.app_version ────────────────────────────────────────────────────────

class TestAppVersion:
    def test_reads_real_version_json(self):
        from utils.app_version import get_app_version
        v = get_app_version()
        assert v and v != "1.0.0", f"unexpected fallback version: {v}"
        assert v[0].isdigit()

    def test_build_tag_format(self):
        from utils.app_version import get_build_tag
        tag = get_build_tag()
        assert tag == "" or "." in tag


# ── utils.company_profile ────────────────────────────────────────────────────

class TestCompanyProfile:
    def test_profile_has_required_keys(self):
        from utils.company_profile import get_company_profile
        p = get_company_profile()
        for key in ("company_name_ar", "product_name_ar", "window_title_ar"):
            assert p.get(key), f"missing {key}"

    def test_missing_file_falls_back_to_defaults(self, tmp_path, monkeypatch):
        import utils.company_profile as cp
        monkeypatch.setattr(cp, "_candidate_paths", lambda: (tmp_path / "nope.json",))
        cp.reset_profile_cache()
        p = cp.get_company_profile()
        assert p["company_name_ar"]
        cp.reset_profile_cache()

    def test_custom_brand_overrides_defaults(self, tmp_path, monkeypatch):
        import utils.company_profile as cp
        custom = tmp_path / "company_profile.json"
        custom.write_text(
            json.dumps({"company_name_ar": "مكتب تجريبي"}), encoding="utf-8"
        )
        monkeypatch.setattr(cp, "_candidate_paths", lambda: (custom,))
        cp.reset_profile_cache()
        assert cp.get_company_profile()["company_name_ar"] == "مكتب تجريبي"
        cp.reset_profile_cache()


# ── utils.i18n ───────────────────────────────────────────────────────────────

class TestI18n:
    def test_arabic_default_returns_original(self):
        from utils import i18n
        i18n.set_language("ar")
        assert i18n.tr("إغلاق") == "إغلاق"

    def test_english_pack_translates_known_keys(self):
        from utils import i18n
        i18n.set_language("en")
        try:
            assert i18n.tr("إغلاق") == "Close"
        finally:
            i18n.set_language("ar")

    def test_unknown_key_returns_original(self):
        from utils import i18n
        i18n.set_language("en")
        try:
            assert i18n.tr("نص غير موجود في الحزمة") == "نص غير موجود في الحزمة"
        finally:
            i18n.set_language("ar")

    def test_missing_language_pack_is_empty(self):
        from utils import i18n
        assert i18n.load_language("xx") == {}


# ── utils.update_checker ─────────────────────────────────────────────────────

class TestUpdateChecker:
    def test_version_tuple_ordering(self):
        from utils.update_checker import _version_tuple
        assert _version_tuple("3.2") > _version_tuple("3.1.9")
        assert _version_tuple("3.10") > _version_tuple("3.9")
        assert _version_tuple("3.1") == _version_tuple("3.1.0")

    def test_disabled_when_no_url(self):
        from utils.update_checker import UpdateInfo, check_for_update
        info = check_for_update()
        assert isinstance(info, UpdateInfo)
        assert info.update_available is False
        assert info.error == "disabled"

    def test_bad_url_returns_error_not_raise(self, monkeypatch):
        from utils import update_checker as uc
        monkeypatch.setattr(
            uc, "get_company_profile", lambda: {"update_check_url": "http://127.0.0.1:9/none"}
        )
        info = uc.check_for_update(timeout=1)
        assert info.update_available is False
        assert info.error


# ── engine.boq_importer multi-column ─────────────────────────────────────────

class TestBoqImporterMultiColumn:
    def _write_xlsx(self, tmp_path, rows_by_col: dict[int, list]):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        max_col = max(rows_by_col)
        for row_idx in range(max(len(v) for v in rows_by_col.values())):
            for col, items in rows_by_col.items():
                if row_idx < len(items):
                    ws.cell(row=row_idx + 1, column=col, value=items[row_idx])
        path = tmp_path / "boq.xlsx"
        wb.save(path)
        return path

    def test_auto_detect_picks_descriptive_column(self, tmp_path):
        from engine.boq_importer import read_boq
        path = self._write_xlsx(tmp_path, {
            1: ["1", "2", "3"],
            2: ["أ-100", "ب-200", "ج-300"],
            3: ["حفر خنادق للشبكات", "تمديدات مياه الشرب", "اختبارات ضغط"],
        })
        items = read_boq(path)
        assert items == ["حفر خنادق للشبكات", "تمديدات مياه الشرب", "اختبارات ضغط"]

    def test_explicit_column_still_works(self, tmp_path):
        from engine.boq_importer import read_boq
        path = self._write_xlsx(tmp_path, {1: ["بند أول"], 2: ["بند ثانٍ أطول"]})
        assert read_boq(path, column=1) == ["بند أول"]

    def test_missing_file_raises_arabic_error(self, tmp_path):
        from engine.boq_importer import BOQImportError, read_boq
        with pytest.raises(BOQImportError):
            read_boq(tmp_path / "ghost.xlsx")

    def test_empty_sheet_raises(self, tmp_path):
        from engine.boq_importer import BOQImportError, read_boq
        path = self._write_xlsx(tmp_path, {1: ["", ""]})
        with pytest.raises(BOQImportError):
            read_boq(path, column=1)
