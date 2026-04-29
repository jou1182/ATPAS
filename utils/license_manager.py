#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ATPAS Machine-Bound License Manager
====================================
كل ترخيص مرتبط بجهاز واحد فقط عبر بصمة رقمية فريدة.
لا يمكن نقل الترخيص أو مشاركته — من اشترى، يشغّل على جهازه فقط.

تدفق العمل:
  1. المستخدم يشتري الكورس/البرنامج
  2. يرسل Machine ID (16 حرف يظهر في نافذة التفعيل)
  3. المطور يُولّد License Key باستخدام generate_key_for_machine()
  4. المستخدم يُدخل الـ Key → يُفعَّل البرنامج على جهازه
  5. أي جهاز آخر → مفتاح مختلف → لا يعمل

الملف المحفوظ: license.dat (في مجلد التطبيق)
"""

from __future__ import annotations

import hashlib
import platform
import uuid
from pathlib import Path
from typing import Tuple

# ---------------------------------------------------------------------------
# Internal secret — NEVER change after first release (breaks existing keys)
# Obfuscated: XOR each byte with 0x5A so it doesn't appear as plain text
# in strings dumps or memory scans.
# ---------------------------------------------------------------------------
_OBF = [
    0x1B, 0x2E, 0x37, 0x12, 0x0B, 0x24, 0x37, 0x00,
    0x18, 0x26, 0x3E, 0x11, 0x08, 0x37, 0x28, 0x3F,
    0x25, 0x3C, 0x38, 0x09, 0x1D, 0x3B, 0x38, 0x0E,
]
_ATPAS_SECRET: str = "".join(chr(b ^ 0x5A) for b in _OBF)

_LICENSE_FILE = Path("license.dat")


# ---------------------------------------------------------------------------
# Machine fingerprint
# ---------------------------------------------------------------------------

def get_machine_id() -> str:
    """Return a stable 16-character uppercase fingerprint for this machine.

    Combines:
      - Network adapter MAC address  (hardware)
      - Windows MachineGuid registry (OS installation identity)
      - Processor string             (partial, for extra entropy)

    The result is hashed so none of the raw values are exposed.
    """
    components: list[str] = []

    # 1. MAC address (survives OS reinstall on same hardware)
    components.append(str(uuid.getnode()))

    # 2. Windows Machine GUID (survives hardware swaps on same OS install)
    try:
        import winreg  # noqa: PLC0415
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        )
        guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        components.append(str(guid))
    except Exception:
        components.append("no-guid")

    # 3. Processor (partial — binds to CPU architecture)
    components.append(platform.processor()[:24])

    raw = "|".join(components)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    return f"{digest[0:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


# ---------------------------------------------------------------------------
# Key generation & verification
# ---------------------------------------------------------------------------

def generate_key_for_machine(machine_id: str) -> str:
    """Developer tool: generate a valid license key for a given Machine ID.

    Run this on the developer's side after the customer sends their
    Machine ID.  Never ship this function in a way that's easy to call —
    it's the "key factory".

    Example:
        >>> generate_key_for_machine("A1B2-C3D4-E5F6-G7H8")
        'ATPAS-XXXXX-XXXXX-XXXXX-XXXXX'
    """
    machine_id = machine_id.replace("-", "").upper()
    raw = f"{machine_id}:{_ATPAS_SECRET}:ATPAS-2026"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
    return f"ATPAS-{digest[0:5]}-{digest[5:10]}-{digest[10:15]}-{digest[15:20]}"


def verify_license(license_key: str) -> bool:
    """Return True if license_key is valid for THIS machine."""
    machine_id = get_machine_id()
    expected = generate_key_for_machine(machine_id)
    return license_key.strip().upper() == expected.upper()


# ---------------------------------------------------------------------------
# Activation state
# ---------------------------------------------------------------------------

def is_activated() -> bool:
    """Return True if a valid license is stored for this machine."""
    if not _LICENSE_FILE.exists():
        return False
    try:
        stored = _LICENSE_FILE.read_text(encoding="utf-8").strip()
        return verify_license(stored)
    except Exception:
        return False


def activate(license_key: str) -> Tuple[bool, str]:
    """Attempt activation with the given key.

    Returns:
        (True,  success_message_ar)  on success
        (False, error_message_ar)    on failure
    """
    if verify_license(license_key):
        try:
            _LICENSE_FILE.write_text(
                license_key.strip().upper(), encoding="utf-8"
            )
        except OSError as exc:
            return False, f"تعذّر حفظ ملف الترخيص: {exc}"
        return True, "تم التفعيل بنجاح ✅\nمرحباً بك في نظام ATPAS."
    return (
        False,
        "مفتاح الترخيص غير صحيح ❌\n"
        "تأكد من:\n"
        "  • نسخ المفتاح كاملاً دون مسافات إضافية\n"
        "  • أن المفتاح صدر لهذا الجهاز تحديداً",
    )


def revoke() -> None:
    """Remove the stored license (for testing / uninstall)."""
    if _LICENSE_FILE.exists():
        _LICENSE_FILE.unlink(missing_ok=True)
