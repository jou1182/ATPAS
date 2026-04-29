#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS — نقطة الدخول الرئيسية للتطبيق المجمّع (EXE)."""

import json
import sys
import os
from pathlib import Path


def _read_version() -> str:
    """Read the application version from version.json.

    Falls back to "unknown" so a missing file never crashes startup.
    version.json is the single source of truth — never hardcode the version
    string inside Python files.
    """
    try:
        with open("version.json", encoding="utf-8") as f:
            return str(json.load(f).get("version", "unknown"))
    except (OSError, ValueError, KeyError):
        return "unknown"


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

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from ui.main_window import MainWindow

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ATPAS")
    app.setApplicationDisplayName("نظام بناء العروض الفنية - الرواف")
    app.setApplicationVersion(_read_version())
    app.setOrganizationName("Al-Rawaf Contracting")

    # ── Apply theme ────────────────────────────────────────────────────
    from ui.theme import apply_palette, get_stylesheet, load_fonts
    load_fonts()
    apply_palette(app)
    app.setStyleSheet(get_stylesheet())

    window = MainWindow(
        registry_path="codes_registry.json",
        config_path="master_config.json",
    )
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
