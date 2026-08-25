#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فاحص التحديثات — بنية تحتية جاهزة للتوزيع العالمي.

الآلية:
  1. يقرأ ``update_check_url`` من company_profile.json.
  2. إن كان فارغاً (الافتراضي) يعمل الوضع الصامت: لا شيء يحدث.
  3. عند توفير رابط يُعيد JSON بالشكل:
         {"version": "3.2", "download_url": "https://...", "notes_ar": "..."}
     يقارنه بإصدار التطبيق المحلي من version.json.

هذا الفصل يجعل نشر تحديث لاحقاً مسألة استضافة ملف JSON واحد فقط،
بدون أي تعديل في كود العميل.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass

from utils.app_version import get_app_version, get_build_tag
from utils.company_profile import get_company_profile

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class UpdateInfo:
    """نتيجة فحص التحديث."""

    update_available: bool
    current_version: str
    latest_version: str = ""
    download_url: str = ""
    notes_ar: str = ""
    error: str = ""


def _version_tuple(version: str) -> tuple:
    """حوّل '3.2.1' إلى (3, 2, 1) للمقارنة الرقمية الآمنة.

    تهمل الأصفار اللاحقة حتى تتكافأ 3.1 مع 3.1.0.
    """
    parts = []
    for chunk in version.strip().split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts) or (0,)


def check_for_update(timeout: int = _TIMEOUT_SECONDS) -> UpdateInfo:
    """افحص الخادم عن إصدار أحدث.

    لا يرمي استثناءات أبداً — أي فشل يعود كـ UpdateInfo(error=...).
    """
    current = get_app_version()
    url = get_company_profile().get("update_check_url", "").strip()
    if not url:
        return UpdateInfo(
            update_available=False,
            current_version=current,
            error="disabled",
        )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"ATPAS/{current}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        latest = str(payload.get("version", "")).strip()
        available = bool(latest) and _version_tuple(latest) > _version_tuple(current)
        return UpdateInfo(
            update_available=available,
            current_version=current,
            latest_version=latest,
            download_url=str(payload.get("download_url", "")),
            notes_ar=str(payload.get("notes_ar", "")),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Update check failed: %s", exc)
        return UpdateInfo(
            update_available=False,
            current_version=current,
            error=str(exc),
        )


__all__ = ["UpdateInfo", "check_for_update"]

# وسم البناء متاح للمستقبل (إرساله في ترويسة الفحص مثلاً)
_BUILD_TAG = get_build_tag
