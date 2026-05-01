#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام ترخيص ATPAS — License Manager
====================================
آلية الحماية:
  - كل كود مربوط بـ Hardware ID فريد للجهاز (Machine GUID + MAC)
  - الكود يحتوي على تاريخ الانتهاء مُضمَّن داخله
  - التحقق يتم بالكامل بدون إنترنت (Offline)
  - لا يعمل الكود على جهاز غير الجهاز الأصلي

تنسيق الكود:
  ATPAS-XXXX-XXXXXXXXXXXX
  │     │    └─ 12 حرف = توقيع HMAC
  │     └────── 4 حرف  = تاريخ الانتهاء (hex days منذ 2024-01-01)
  └──────────── بادئة ثابتة

مثال:  ATPAS-0168-A3F29C1B4D7E
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import platform
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ── المفتاح السري — مقسّم لمنع الاكتشاف السهل ──────────────────────────
# (في الإنتاج: يُشفَّر أو يُوزَّع على أجزاء أكثر)
_P1 = b"\x52\x61\x77\x61\x66"      # Rawaf
_P2 = b"\x2d\x41\x54\x50\x41\x53"  # -ATPAS
_P3 = b"\x2d\x4c\x49\x43\x2d"      # -LIC-
_P4 = b"\x32\x30\x32\x34\x58\x39"  # 2024X9
_HMAC_KEY: bytes = _P1 + _P2 + _P3 + _P4

# ── نقطة مرجعية للتاريخ ──────────────────────────────────────────────────
_EPOCH = datetime(2024, 1, 1)

# ── Cache بصمة الجهاز — تُحسب مرة واحدة فقط per-process ─────────────────
# platform.node() يستدعي WMI query (~300ms) — التخزين يُلغي هذه التكلفة
# من كل عملية تحقق لاحقة خلال نفس الجلسة.
_hw_id_cache: str | None = None

# ── Cache نتيجة فحص الترخيص المحفوظ ──────────────────────────────────────
# check_saved_license() تستدعي get_hardware_id() مع كل بناء وثيقة.
# الترخيص لا يتغير أثناء الجلسة، لذا نخزّن النتيجة ونُبطلها فقط عند
# تفعيل ترخيص جديد (activate_license يستدعي invalidate_license_cache).
_license_check_cache: "dict | None" = None


def invalidate_license_cache() -> None:
    """أبطل cache نتيجة الترخيص. استدعِها بعد تفعيل ترخيص جديد."""
    global _license_check_cache
    _license_check_cache = None

# ── مسار ملف الترخيص المحفوظ ─────────────────────────────────────────────
def _license_path() -> Path:
    """يُخزَّن في %APPDATA%/ATPAS/license.dat على Windows."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    folder = base / "ATPAS"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "license.dat"


# ════════════════════════════════════════════════════════════════════════════
# بصمة الجهاز
# ════════════════════════════════════════════════════════════════════════════

def get_hardware_id() -> str:
    """
    يولّد معرّفاً فريداً وثابتاً لهذا الجهاز.
    يجمع بين: Windows Machine GUID + MAC Address + اسم الجهاز.
    النتيجة: XXXX-XXXX-XXXX-XXXX (16 حرف hex بصيغة مقسّمة)

    النتيجة مُخزَّنة (cached) per-process لأن platform.node() يستدعي
    WMI query على Windows وتستغرق ~300ms في أول استدعاء.
    """
    global _hw_id_cache
    if _hw_id_cache is not None:
        return _hw_id_cache

    parts: list[str] = []

    # 1. Windows Machine GUID — الأكثر ثباتاً
    if sys.platform == "win32":
        try:
            import winreg  # type: ignore[import]
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            )
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            parts.append(str(guid))
        except Exception:
            pass

    # 2. MAC Address
    mac = uuid.getnode()
    parts.append(f"{mac:012x}")

    # 3. اسم الجهاز
    parts.append(platform.node().lower())

    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    hw = digest[:16].upper()
    _hw_id_cache = f"{hw[0:4]}-{hw[4:8]}-{hw[8:12]}-{hw[12:16]}"
    return _hw_id_cache


# ════════════════════════════════════════════════════════════════════════════
# توليد الكود (يستخدمه المطوّر فقط — لا يُضمَّن في EXE العميل)
# ════════════════════════════════════════════════════════════════════════════

def generate_key(hardware_id: str, days_valid: int = 365) -> str:
    """
    يولّد كود ترخيص مربوط بـ hardware_id وصالح لمدة days_valid يوماً.

    Args:
        hardware_id: بصمة جهاز العميل (يحصل عليها من شاشة التفعيل)
        days_valid:  مدة الصلاحية بالأيام (افتراضي: 365)

    Returns:
        كود بصيغة ATPAS-XXXX-XXXXXXXXXXXX
    """
    hw_clean = hardware_id.replace("-", "").upper()

    # تاريخ الانتهاء كعدد أيام منذ _EPOCH
    expiry_dt = datetime.now() + timedelta(days=days_valid)
    expiry_days = (expiry_dt - _EPOCH).days           # عدد صحيح
    expiry_hex  = f"{expiry_days:04X}"                # 4 حروف hex

    # التوقيع: HMAC(secret, hw + expiry_hex)
    payload = f"{hw_clean}:{expiry_hex}".encode("utf-8")
    sig = hmac.new(_HMAC_KEY, payload, hashlib.sha256).hexdigest()[:12].upper()

    return f"ATPAS-{expiry_hex}-{sig}"


# ════════════════════════════════════════════════════════════════════════════
# التحقق من الكود (يعمل على جهاز العميل)
# ════════════════════════════════════════════════════════════════════════════

def _parse_key(license_key: str) -> tuple[str, str] | None:
    """يفكّك الكود → (expiry_hex, sig) أو None إذا كان التنسيق خاطئاً."""
    key = license_key.strip().upper().replace(" ", "")
    if key.startswith("ATPAS-"):
        key = key[6:]
    parts = key.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 12:
        return None
    return parts[0], parts[1]


def verify_key(license_key: str, hardware_id: str | None = None) -> dict:
    """
    يتحقق من صحة كود الترخيص لهذا الجهاز.

    Returns:
        {
          "valid": bool,
          "message": str,          # رسالة عربية للمستخدم
          "expiry": datetime | None,
          "days_left": int | None,
        }
    """
    if hardware_id is None:
        hardware_id = get_hardware_id()

    parsed = _parse_key(license_key)
    if parsed is None:
        return {
            "valid": False,
            "message": "❌ تنسيق الكود غير صحيح — تأكد من نسخه كاملاً",
            "expiry": None,
            "days_left": None,
        }

    expiry_hex, sig_provided = parsed
    hw_clean = hardware_id.replace("-", "").upper()

    # إعادة حساب التوقيع المتوقع
    payload = f"{hw_clean}:{expiry_hex}".encode("utf-8")
    sig_expected = hmac.new(
        _HMAC_KEY, payload, hashlib.sha256
    ).hexdigest()[:12].upper()

    # مقارنة آمنة (تمنع timing attacks)
    if not hmac.compare_digest(sig_expected, sig_provided):
        return {
            "valid": False,
            "message": "❌ الكود غير صحيح أو لا يطابق هذا الجهاز",
            "expiry": None,
            "days_left": None,
        }

    # فك تشفير تاريخ الانتهاء
    try:
        expiry_days = int(expiry_hex, 16)
        expiry_dt   = _EPOCH + timedelta(days=expiry_days)
    except ValueError:
        return {
            "valid": False,
            "message": "❌ تاريخ انتهاء الترخيص تالف",
            "expiry": None,
            "days_left": None,
        }

    now       = datetime.now()
    days_left = (expiry_dt - now).days

    if expiry_dt < now:
        return {
            "valid": False,
            "message": f"⏰ انتهت صلاحية الترخيص في {expiry_dt.strftime('%Y-%m-%d')}",
            "expiry": expiry_dt,
            "days_left": 0,
        }

    return {
        "valid": True,
        "message": f"✅ مرخّص — صالح حتى {expiry_dt.strftime('%Y-%m-%d')} ({days_left} يوم)",
        "expiry": expiry_dt,
        "days_left": days_left,
    }


# ════════════════════════════════════════════════════════════════════════════
# حفظ واسترجاع الترخيص المُفعَّل
# ════════════════════════════════════════════════════════════════════════════

def activate(license_key: str) -> dict:
    """
    يفعّل الكود ويحفظه. يُستدعى مرة واحدة فقط من شاشة التفعيل.

    Returns: نفس قاموس verify_key + {"activated": bool}
    """
    result = verify_key(license_key)
    if not result["valid"]:
        return {**result, "activated": False}

    hw_id = get_hardware_id()
    data  = {
        "key":          license_key.strip().upper(),
        "hardware_id":  hw_id,
        "activated_at": datetime.now().isoformat(),
        "expiry":       result["expiry"].isoformat() if result["expiry"] else "",
    }
    try:
        _license_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        return {
            "valid": False,
            "activated": False,
            "message": f"❌ تعذّر حفظ الترخيص: {exc}",
            "expiry": None,
            "days_left": None,
        }

    return {**result, "activated": True}


def check_saved_license() -> dict:
    """
    يتحقق من الترخيص المحفوظ عند كل تشغيل.

    النتيجة مُخزَّنة per-process: الترخيص لا يتغير أثناء الجلسة،
    وكل استدعاء كان يُشغّل WMI query (~300ms). بعد أول استدعاء
    تُعاد النتيجة فوراً. استدعِ invalidate_license_cache() بعد تفعيل
    ترخيص جديد حتى تُقرأ القيمة الجديدة.

    Returns:
        {"valid": bool, "message": str, "days_left": int | None}
    """
    global _license_check_cache
    if _license_check_cache is not None:
        return _license_check_cache

    path = _license_path()
    if not path.exists():
        result = {
            "valid": False,
            "message": "البرنامج غير مفعّل — أدخل كود الترخيص للمتابعة",
            "days_left": None,
        }
        _license_check_cache = result
        return result

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        path.unlink(missing_ok=True)
        result = {
            "valid": False,
            "message": "ملف الترخيص تالف — يرجى إعادة التفعيل",
            "days_left": None,
        }
        _license_check_cache = result
        return result

    # تحقق من تطابق الجهاز
    current_hw = get_hardware_id()
    if data.get("hardware_id") != current_hw:
        result = {
            "valid": False,
            "message": "الترخيص لا يطابق هذا الجهاز",
            "days_left": None,
        }
        _license_check_cache = result
        return result

    # إعادة التحقق الكامل من الكود
    result = verify_key(data.get("key", ""), current_hw)
    _license_check_cache = result
    return result


def get_license_info() -> dict:
    """معلومات مختصرة للعرض في شاشة 'عن النظام'."""
    result = check_saved_license()
    hw_id  = get_hardware_id()
    return {
        "valid":     result["valid"],
        "message":   result.get("message", ""),
        "days_left": result.get("days_left"),
        "hardware_id": hw_id,
    }
