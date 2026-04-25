#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS error-handling utilities.

arabic_message  — maps an exception to a short Arabic user label.
format_user_error — returns a full Arabic message with an actionable hint.
safe_call       — wraps any callable, returning (success, result, error_ar).
"""

import logging
import traceback
from typing import Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Short labels ───────────────────────────────────────────────────────────────
_AR_MESSAGES: dict[str, str] = {
    "FileNotFoundError":  "الملف المطلوب غير موجود",
    "ValueError":         "بيانات غير صالحة",
    "KeyError":           "حقل مفقود في البيانات",
    "PermissionError":    "لا توجد صلاحية للوصول إلى الملف",
    "OSError":            "خطأ في نظام الملفات",
    "IOError":            "خطأ في قراءة أو كتابة الملف",
    "MemoryError":        "الذاكرة غير كافية لإتمام العملية",
    "TimeoutError":       "انتهت المهلة الزمنية للعملية",
    "UnicodeDecodeError": "تعذّر قراءة الملف — تحقق من الترميز (UTF-8)",
    "json.JSONDecodeError": "الملف لا يحتوي على JSON صالح",
    "AttributeError":     "بيانات النظام غير مكتملة",
    "TypeError":          "نوع بيانات غير متوقع",
    "ZeroDivisionError":  "خطأ حسابي في النظام",
    "RecursionError":     "تكرار لا نهائي في التبعيات — تحقق من الأكواد",
    "default":            "حدث خطأ غير متوقع",
}

# ── Actionable hints per error type ───────────────────────────────────────────
_AR_HINTS: dict[str, str] = {
    "FileNotFoundError":  "تأكد من وجود الملف في المسار المطلوب، وأن الاسم مطابق تماماً.",
    "PermissionError":    "أغلق الملف إذا كان مفتوحاً في Word ثم حاول مجدداً.",
    "OSError":            "تحقق من مساحة القرص وصلاحيات المجلد.",
    "IOError":            "تحقق من مساحة القرص وصلاحيات المجلد.",
    "MemoryError":        "أغلق البرامج الأخرى وأعد المحاولة، أو قلّل عدد الأكواد المختارة.",
    "UnicodeDecodeError": "افتح الملف بمحرر نصوص وتأكد من حفظه بترميز UTF-8.",
    "RecursionError":     "يوجد تبعية دائرية في الأكواد — راجع حقل 'dependencies' في السجل.",
    "ValueError":         "تحقق من صيغة البيانات في ملف JSON المرتبط.",
    "KeyError":           "تحقق من أن ملفات الإعداد مكتملة وغير تالفة.",
}


def arabic_message(exc: Exception) -> str:
    """Return a short Arabic label for an exception type.

    Walks the full MRO so subclasses (e.g. json.JSONDecodeError → ValueError)
    are matched correctly, regardless of inheritance depth.
    """
    for cls in type(exc).__mro__:
        if cls.__name__ in _AR_MESSAGES:
            return _AR_MESSAGES[cls.__name__]
    return _AR_MESSAGES["default"]


def format_user_error(exc: Exception, context: str = "") -> str:
    """Return a full Arabic user-facing error string with an actionable hint.

    Format::
        [سياق] — نوع الخطأ: رسالة قصيرة
        💡 التوصية: ...

    Args:
        exc:     The exception to describe.
        context: Optional Arabic context string (e.g. "تحميل السجل").

    Returns:
        Multi-line Arabic string suitable for a QMessageBox or status bar.
    """
    label = arabic_message(exc)
    hint  = _AR_HINTS.get(type(exc).__name__, "")

    parts = []
    if context:
        parts.append(f"[{context}] — {label}")
    else:
        parts.append(label)

    parts.append(f"التفاصيل: {type(exc).__name__}: {exc}")

    if hint:
        parts.append(f"💡 التوصية: {hint}")

    return "\n".join(parts)


def safe_call(
    func: Callable,
    *args: Any,
    context: str = "",
    **kwargs: Any,
) -> Tuple[bool, Any, Optional[str]]:
    """Call *func* safely and return (success, result, error_ar).

    *error_ar* is ``None`` on success.  On failure it is the string returned
    by :func:`format_user_error` so callers can display it directly in the UI.
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as exc:
        msg = format_user_error(exc, context)
        log_msg = f"[{context}] {type(exc).__name__}: {exc}" if context else str(exc)
        logger.error("%s\n%s", log_msg, traceback.format_exc())
        return False, None, msg
