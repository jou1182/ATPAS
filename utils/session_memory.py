#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Smart Session Memory — يحفظ آخر 10 جلسات عمل ويعرضها للاسترجاع السريع.

كل جلسة تحتوي على:
- project_ids: قائمة معرفات المشاريع
- owner_id: معرف الجهة المالكة
- selected_codes: قائمة الأكواد المختارة
- timestamp: وقت الحفظ
- label: اسم وصفي (مثلاً "جلسة 15 مارس 2026")
- code_count: عدد الأكواد
- page_count: إجمالي الصفحات (محسوب وقت الحفظ)

التخزين: ملف JSON بجوار EXE أو في مجلد المشروع.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ── الحد الأقصى لعدد الجلسات المحفوظة ────────────────────────────────
MAX_SESSIONS = 10


@dataclass
class SessionRecord:
    """سجل جلسة عمل واحدة."""

    project_ids: list[str]
    owner_id: str
    selected_codes: list[str]
    timestamp: float          # time.time()
    label: str = ""           # اسم وصفي
    code_count: int = 0
    page_count: int = 0


def _get_storage_path() -> Path:
    """مسار ملف تخزين الجلسات — بجوار EXE أو في مجلد المشروع."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / ".atpas_sessions.json"
    return Path(".atpas_sessions.json")


def _load_all() -> list[dict]:
    """تحميل جميع الجلسات من ملف التخزين."""
    path = _get_storage_path()
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (OSError, json.JSONDecodeError):
        return []


def _save_all(sessions: list[dict]) -> None:
    """حفظ جميع الجلسات إلى ملف التخزين."""
    path = _get_storage_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # فشل الحفظ ليس كارثة


def _make_label(session: dict) -> str:
    """توليد اسم وصفي للجلسة بناءً على محتواها."""
    pids = session.get("project_ids", [])
    oid = session.get("owner_id", "")
    ts = session.get("timestamp", 0)
    n = session.get("code_count", 0)

    # تنسيق التاريخ
    if ts:
        from datetime import datetime
        dt = datetime.fromtimestamp(ts)
        date_str = dt.strftime("%d %b %Y — %I:%M %p")
    else:
        date_str = "تاريخ غير معروف"

    projects = " + ".join(pids) if pids else "?"
    return f"{date_str}  |  {projects}  |  {oid}  |  {n} كود"


def save_session(
    project_ids: list[str],
    owner_id: str,
    selected_codes: list[str],
    registry_codes: dict[str, Any] | None = None,
) -> None:
    """حفظ الجلسة الحالية في قائمة الجلسات (آخر 10)."""
    if not project_ids or not owner_id or not selected_codes:
        return

    # حساب عدد الصفحات
    page_count = 0
    if registry_codes:
        for cid in selected_codes:
            code_info = registry_codes.get(cid, {})
            try:
                page_count += int(code_info.get("page_count", 0))
            except (TypeError, ValueError):
                pass

    record = SessionRecord(
        project_ids=list(project_ids),
        owner_id=owner_id,
        selected_codes=list(selected_codes),
        timestamp=time.time(),
        code_count=len(selected_codes),
        page_count=page_count,
    )

    sessions = _load_all()

    # إزالة أي جلسة مطابقة تماماً (نفس الأكواد والمشروع والجهة) — تجنب التكرار
    sessions = [
        s for s in sessions
        if not (
            s.get("project_ids") == record.project_ids
            and s.get("owner_id") == record.owner_id
            and s.get("selected_codes") == record.selected_codes
        )
    ]

    # إضافة الجلسة الجديدة في البداية
    d = asdict(record)
    d["label"] = _make_label(d)
    sessions.insert(0, d)

    # قص إلى أقصى حد
    sessions = sessions[:MAX_SESSIONS]

    _save_all(sessions)


def get_sessions() -> list[dict]:
    """إرجاع قائمة الجلسات المحفوظة (الأحدث أولاً)."""
    sessions = _load_all()
    for s in sessions:
        if not s.get("label"):
            s["label"] = _make_label(s)
    return sessions


def restore_session(index: int) -> dict | None:
    """استرجاع جلسة حسب index في القائمة (0 = الأحدث)."""
    sessions = get_sessions()
    if 0 <= index < len(sessions):
        return sessions[index]
    return None


def delete_session(index: int) -> bool:
    """حذف جلسة حسب index. تعيد True إذا نجح الحذف."""
    sessions = _load_all()
    if 0 <= index < len(sessions):
        sessions.pop(index)
        _save_all(sessions)
        return True
    return False


def clear_all_sessions() -> None:
    """مسح جميع الجلسات المحفوظة."""
    _save_all([])


def count_sessions() -> int:
    """عدد الجلسات المحفوظة حالياً."""
    return len(_load_all())
