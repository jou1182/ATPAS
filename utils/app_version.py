#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""قراءة رقم إصدار التطبيق من version.json — المصدر الوحيد للإصدار.

يستخدمه main.py وشريط الهيدر وأي مكان يحتاج رقم الإصدار،
بدلاً من تثبيت أرقام مختلفة في مواضع متفرقة.
"""

from __future__ import annotations

import json
from pathlib import Path

_FALLBACK = "1.0.0"


def get_app_version() -> str:
    """يعيد رقم الإصدار من version.json أو القيمة الاحتياطية عند غيابه."""
    candidates = (
        Path("version.json"),
        Path(__file__).resolve().parent.parent / "version.json",
    )
    for candidate in candidates:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            version = str(data.get("version", "")).strip()
            if version:
                return version
        except (OSError, ValueError):
            continue
    return _FALLBACK


def get_build_tag() -> str:
    """يعيد وسم البناء الكامل مثل 3.1.20260504 أو سلسلة فارغة."""
    try:
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "version.json")
            .read_text(encoding="utf-8")
        )
        return str(data.get("build_tag", "")).strip()
    except (OSError, ValueError):
        return ""
