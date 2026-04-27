#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from openpyxl import Workbook
from engine.boq_importer import read_boq, BOQImportError


def _make_xlsx(rows: list, tmp_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    path = tmp_path / "test_boq.xlsx"
    wb.save(path)
    return path


def test_reads_simple_list(tmp_path):
    path = _make_xlsx([["حفر بالميكنة"], ["خرسانة عادية"], ["أعمال صرف"]], tmp_path)
    result = read_boq(str(path))
    assert result == ["حفر بالميكنة", "خرسانة عادية", "أعمال صرف"]


def test_includes_all_non_empty_rows(tmp_path):
    path = _make_xlsx([["اسم البند"], ["حفر بالميكنة"], ["خرسانة عادية"]], tmp_path)
    result = read_boq(str(path))
    assert "حفر بالميكنة" in result
    assert "خرسانة عادية" in result


def test_skips_empty_rows(tmp_path):
    path = _make_xlsx([["حفر"], [""], [None], ["خرسانة"]], tmp_path)
    result = read_boq(str(path))
    assert result == ["حفر", "خرسانة"]


def test_raises_on_missing_file():
    with pytest.raises(BOQImportError, match="الملف غير موجود"):
        read_boq("nonexistent.xlsx")


def test_raises_on_empty_file(tmp_path):
    path = _make_xlsx([], tmp_path)
    with pytest.raises(BOQImportError, match="لا توجد بنود"):
        read_boq(str(path))


def test_raises_on_corrupt_file(tmp_path):
    bad = tmp_path / "bad.xlsx"
    bad.write_bytes(b"not a zip")
    with pytest.raises(BOQImportError):
        read_boq(bad)
