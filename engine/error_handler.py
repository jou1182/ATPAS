#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import traceback
from typing import Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# Arabic user-facing messages for common error types
_AR_MESSAGES = {
    "FileNotFoundError": "الملف المطلوب غير موجود",
    "ValueError": "بيانات غير صالحة",
    "KeyError": "حقل مفقود في البيانات",
    "PermissionError": "لا توجد صلاحية للوصول إلى الملف",
    "OSError": "خطأ في نظام الملفات",
    "MemoryError": "الذاكرة غير كافية لإتمام العملية",
    "default": "حدث خطأ غير متوقع",
}


def arabic_message(exc: Exception) -> str:
    """Return Arabic user-facing message for an exception."""
    return _AR_MESSAGES.get(type(exc).__name__, _AR_MESSAGES["default"])


def safe_call(func: Callable, *args, context: str = "", **kwargs) -> Tuple[bool, Any, Optional[str]]:
    """
    Call func(*args, **kwargs) safely.

    Returns:
        (success, result, error_message_ar) — error_message_ar is None on success.
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as exc:
        ar_msg = arabic_message(exc)
        detail = f"{type(exc).__name__}: {exc}"
        log_msg = f"[{context}] {detail}" if context else detail
        logger.error("%s\n%s", log_msg, traceback.format_exc())
        return False, None, f"{ar_msg} — {detail}"
