#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from openpyxl import load_workbook


class BOQImportError(Exception):
    pass


def read_boq(filepath: str | Path) -> list[str]:
    """
    يقرأ ملف Excel ويُرجع قائمة أسماء البنود النظيفة.

    Args:
        filepath: مسار ملف .xlsx أو .xls

    Returns:
        list[str] — أسماء البنود (stripped, non-empty)

    Raises:
        BOQImportError: إذا الملف غير موجود أو فارغ
    """
    path = Path(filepath)
    if not path.exists():
        raise BOQImportError(f"الملف غير موجود: {filepath}")

    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        raise BOQImportError(f"تعذّر قراءة الملف: {filepath}") from exc

    items: list[str] = []
    try:
        ws = wb.active
        for row in ws.iter_rows(min_col=1, max_col=1, values_only=True):
            cell = row[0]
            if cell is None:
                continue
            text = str(cell).strip()
            if text:
                items.append(text)
    finally:
        wb.close()

    if not items:
        raise BOQImportError("لا توجد بنود في الملف")

    return items
