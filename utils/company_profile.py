#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""الملف التعريفي للشركة — White-label single source of truth.

يجعل ATPAS قابلاً لإعادة التوزيع لأي مكتب هندسي أو شركة مقاولات دون تعديل
الكود: كل ما يخص هوية الشركة (الاسم، الشعار النصي، روابط التواصل) يُقرأ من
``company_profile.json`` بجوار التطبيق، مع قيم افتراضية لشركة الرواف.

لاستخدام نسخة بعلامة تجارية أخرى:
    انسخ company_profile.json وعدّل قيمه — لا حاجة لبناء جديد.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DEFAULT_PROFILE: dict = {
    "company_name_ar": "الرواف",
    "company_name_en": "Al-Rawaf",
    "product_name_ar": "نظام بناء العروض الفنية",
    "window_title_ar": "نظام بناء العروض الفنية - الرواف",
    "publisher_ar": "الرواف للهندسة والتقنية",
    "publisher_en": "Al-Rawaf Engineering",
    "support_email": "jou1182@gmail.com",
    "support_whatsapp": "",
}


def _candidate_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parent.parent
    return (
        Path("company_profile.json"),
        root / "company_profile.json",
    )


@lru_cache(maxsize=1)
def get_company_profile() -> dict:
    """يعيد ملف الهوية مدموجاً فوق الافتراضي (نتيجة مخزّنة لكل عملية)."""
    profile = dict(_DEFAULT_PROFILE)
    for candidate in _candidate_paths():
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                profile.update({k: v for k, v in data.items() if isinstance(v, str)})
            break
        except (OSError, ValueError):
            continue
    return profile


def reset_profile_cache() -> None:
    """يفسح الكاش — يُستدعى بعد تعديل company_profile.json أثناء التشغيل."""
    get_company_profile.cache_clear()
