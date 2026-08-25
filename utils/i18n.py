#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بنية الترجمة — خطوة ATPAS نحو منصة عالمية (i18n).

الفكرة:
  * ``tr("مسح وتثبيت نقاط عامة")`` تعيد النص كما هو في العربية (الافتراضي).
  * عند تحميل حزمة لغة (``i18n/en.json`` مثلاً) تُستخدم الترجمة المقابلة.
  * الحزمة ملف JSON بسيط: {"النص العربي الأصلي": "English text"}.

خطة التبني التدريجي:
  المرحلة أ — هذه الوحدة متاحة، والواجهة تبقى عربية (لا تغيير سلوكي).
  المرحلة ب — استبدال النصوص المركزية تدريجياً بـ tr(...) بدءاً من القوائم.
  المرحلة ج — إضافة RTL/LTR switching مع حزمة en.json مكتملة.

هذا يحقق الجاهزية العالمية دون هندسة عكسية ضخمة دفعة واحدة.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_LANG_DIR_NAME = "i18n"


@lru_cache(maxsize=8)
def load_language(lang: str) -> dict[str, str]:
    """حمّل حزمة لغة من ``i18n/<lang>.json``؛ العربية الأصلية إن لم توجد."""
    if not lang or lang == "ar":
        return {}
    root = Path(__file__).resolve().parent.parent
    for candidate in (
        Path(_LANG_DIR_NAME) / f"{lang}.json",
        root / _LANG_DIR_NAME / f"{lang}.json",
    ):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if isinstance(v, str)}
        except (OSError, ValueError):
            continue
    logger.warning("Language pack not found: %s", lang)
    return {}


def set_language(lang: str) -> None:
    """فعّل اللغة الحالية للعملية (تُطبق على نداءات tr اللاحقة)."""
    global _CURRENT_LANG
    _CURRENT_LANG = lang
    load_language.cache_clear()
    # أعد التحميل فوراً حتى تُختبر الحزمة هنا وليس عند أول ترجمة
    load_language(lang)


_CURRENT_LANG = "ar"


def get_language() -> str:
    """اللغة النشطة حالياً."""
    return _CURRENT_LANG


def available_languages() -> list[str]:
    """قائمة اللغات المتوفرة فعلياً في مجلد i18n (على الأقل العربية)."""
    root = Path(__file__).resolve().parent.parent / _LANG_DIR_NAME
    langs = ["ar"]
    if root.exists():
        langs.extend(p.stem for p in root.glob("*.json"))
    return sorted(set(langs))


def tr(text_ar: str) -> str:
    """ترجم نصاً عربياً إلى اللغة النشطة (يعيد الأصل إن لم توجد ترجمة)."""
    pack = load_language(_CURRENT_LANG)
    if not pack:
        return text_ar
    return pack.get(text_ar, text_ar)
