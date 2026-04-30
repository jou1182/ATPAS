#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS — نقطة الدخول الرئيسية للتطبيق المجمّع (EXE)."""

import sys
import os
from pathlib import Path


def _fix_working_dir() -> None:
    """
    When frozen (EXE), data files land in sys._MEIPASS (_internal/).
    Set CWD there so relative paths resolve correctly.
    Output files go next to the EXE, not inside _internal.
    """
    if getattr(sys, "frozen", False):
        # sys._MEIPASS = .../dist/ATPAS/_internal/
        os.chdir(sys._MEIPASS)  # type: ignore[attr-defined]


def main() -> int:
    _fix_working_dir()

    # ── DPI: يجب إعداده قبل إنشاء QApplication ─────────────────────────
    # PassThrough يمنع تقريب عامل التكبير — يعطي صورة حادة على كل شاشة
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from ui.main_window import MainWindow

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ATPAS")
    app.setApplicationDisplayName("نظام بناء العروض الفنية - الرواف")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Al-Rawaf Contracting")

    # ── Apply theme ────────────────────────────────────────────────────
    from ui.theme import apply_palette, get_stylesheet, load_fonts
    load_fonts()
    apply_palette(app)
    app.setStyleSheet(get_stylesheet())

    # ── التحقق من الترخيص ──────────────────────────────────────────────
    from utils.license_manager import check_saved_license
    from ui.activation_dialog import ActivationDialog

    license_status = check_saved_license()
    if not license_status["valid"]:
        dlg = ActivationDialog(message=license_status["message"])
        if dlg.exec_() != ActivationDialog.Accepted or not dlg.was_activated():
            return 0   # المستخدم أغلق شاشة التفعيل → لا يفتح البرنامج

    # ── فتح النافذة الرئيسية ───────────────────────────────────────────
    window = MainWindow(
        registry_path="codes_registry.json",
        config_path="master_config.json",
    )
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
