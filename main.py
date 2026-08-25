#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS — نقطة الدخول الرئيسية للتطبيق المجمّع (EXE)."""

import logging
import os
import sys
from pathlib import Path

# ── رقم الإصدار — يُقرأ من version.json (المصدر الوحيد) ─────────────────
APP_VERSION = "1.0.0"   # احتياطي فقط؛ تُحدَّث داخل main() بعد ضبط مجلد العمل
# ─────────────────────────────────────────────────────────────────────────────

_EXPIRY_WARNING_DAYS = 7   # عدد الأيام التي يُظهَر فيها التحذير قبل الانتهاء


def _fix_working_dir() -> None:
    """
    When frozen (EXE), data files land in sys._MEIPASS (_internal/).
    Set CWD there so relative paths resolve correctly.
    Output files go next to the EXE, not inside _internal.
    """
    if getattr(sys, "frozen", False):
        # sys._MEIPASS = .../dist/ATPAS/_internal/
        os.chdir(sys._MEIPASS)  # type: ignore[attr-defined]


def _setup_logging() -> None:
    """إعداد نظام تسجيل الأخطاء في %APPDATA%/ATPAS/logs/atpas.log."""
    try:
        logs_dir = Path(os.environ.get("APPDATA", Path.home())) / "ATPAS" / "logs"
        from engine.logger import setup_logging
        setup_logging(logs_dir=logs_dir, level=logging.INFO)
        logging.getLogger("atpas.main").info(
            "ATPAS v%s started — logs: %s", APP_VERSION, logs_dir
        )
    except Exception:
        pass   # لا يوقف البرنامج إذا فشل الـ logging


def main() -> int:
    global APP_VERSION
    _fix_working_dir()

    # الإصدار الحقيقي من version.json بعد ضبط مجلد العمل
    try:
        from utils.app_version import get_app_version
        APP_VERSION = get_app_version()
    except Exception:
        pass

    _setup_logging()

    # ── DPI: يجب إعداده قبل إنشاء QApplication ─────────────────────────
    # PassThrough يمنع تقريب عامل التكبير — يعطي صورة حادة على كل شاشة
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from ui.main_window import MainWindow

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ATPAS")
    # عنوان النافذة من company_profile.json — قابل لإعادة التوزيع بعلامة أخرى
    from utils.company_profile import get_company_profile
    app.setApplicationDisplayName(get_company_profile()["window_title_ar"])
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(get_company_profile().get("publisher_en", "ATPAS"))

    # ── Apply theme ────────────────────────────────────────────────────
    from ui.theme import apply_palette, get_stylesheet, load_fonts
    from ui.theme import get_font
    load_fonts()
    app.setFont(get_font())
    apply_palette(app)
    app.setStyleSheet(get_stylesheet())

    # ── التحقق من الترخيص أو التجربة ──────────────────────────────────
    from utils.license_manager import has_active_trial_or_license
    from ui.activation_dialog import ActivationDialog

    license_status = has_active_trial_or_license()
    if not license_status["valid"]:
        dlg = ActivationDialog(message=license_status["message"])
        if dlg.exec_() != ActivationDialog.Accepted or not dlg.was_activated():
            return 0   # المستخدم أغلق شاشة التفعيل → لا يفتح البرنامج
        # أعد قراءة الترخيص بعد التفعيل أو التجربة
        license_status = has_active_trial_or_license()

    days_left = license_status.get("days_left")

    # ── فتح النافذة الرئيسية ───────────────────────────────────────────
    window = MainWindow(
        registry_path="codes_registry.json",
        config_path="master_config.json",
    )
    window.show()

    # ── تحذير انتهاء الترخيص (يظهر بعد 800ms من فتح النافذة) ──────────
    if days_left is not None and 0 < days_left <= _EXPIRY_WARNING_DAYS:
        from utils.license_manager import get_hardware_id
        expiry_str = license_status.get("expiry", "")
        if hasattr(expiry_str, "strftime"):
            expiry_str = expiry_str.strftime("%Y-%m-%d")
        hw_id = get_hardware_id()

        from ui.expiry_warning_dialog import ExpiryWarningDialog

        def _show_expiry_warning():
            dlg = ExpiryWarningDialog(
                days_left=days_left,
                expiry_date=str(expiry_str),
                hardware_id=hw_id,
                parent=window,
            )
            dlg.exec_()

        QTimer.singleShot(800, _show_expiry_warning)
        logging.getLogger("atpas.main").warning(
            "License expiring in %d day(s).", days_left
        )

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
