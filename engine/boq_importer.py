#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from openpyxl import load_workbook

# أدنى طول لنص يُعدّ بنداً مرشحاً عند الكشف التلقائي عن العمود
_MIN_ITEM_LEN = 6


class BOQImportError(Exception):
    pass


def read_boq(filepath: str | Path, column: int | None = None) -> list[str]:
    """
    يقرأ ملف Excel ويُرجع قائمة أسماء البنود النظيفة.

    Args:
        filepath: مسار ملف .xlsx أو .xls
        column:   رقم العمود المطلوب (1 = A كما في الإصدارات السابقة).
                  الافتراضي None = كشف تلقائي للعمود الأغنى بنصوص وصفية.

    Returns:
        list[str] — أسماء البنود (stripped, non-empty)

    Raises:
        BOQImportError: إذا الملف غير موجود أو فارغ أو العمود خارج النطاق
    """
    path = Path(filepath)
    if not path.exists():
        raise BOQImportError(f"الملف غير موجود: {filepath}")

    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        raise BOQImportError(f"تعذّر قراءة الملف: {filepath}") from exc

    try:
        ws = wb.active
        if column is not None:
            return _read_column(ws, int(column))

        # الكشف التلقائي: اختر العمود صاحب أكبر عدد من النصوص الوصفية
        rows = list(ws.iter_rows(values_only=True))
        max_col = max((len(r) for r in rows), default=0)
        best_col, best_score, best_items = 1, -1, []
        for col in range(1, max_col + 1):
            items = _collect_text_column(rows, col - 1)
            score = sum(1 for t in items if len(t) >= _MIN_ITEM_LEN)
            if score > best_score:
                best_col, best_score, best_items = col, score, items
        if best_score <= 0:
            raise BOQImportError("لا توجد بنود نصية في الملف")
        return best_items
    finally:
        wb.close()


def _read_column(ws, column: int) -> list[str]:
    """اقرأ عموداً محدداً (1-based) من ورقة نشطة."""
    items: list[str] = []
    for row in ws.iter_rows(min_col=column, max_col=column, values_only=True):
        cell = row[0]
        if cell is None:
            continue
        text = str(cell).strip()
        if text:
            items.append(text)
    if not items:
        raise BOQImportError(f"لا توجد بنود في العمود {column}")
    return items


def _collect_text_column(rows: list[tuple], col_index: int) -> list[str]:
    """اجمع الخلايا النصية فقط من عمود (0-based) مع تجاهل الأرقام والتواريخ."""
    items: list[str] = []
    for row in rows:
        if col_index >= len(row):
            continue
        cell = row[col_index]
        if isinstance(cell, str):
            text = cell.strip()
            if text:
                items.append(text)
    return items
