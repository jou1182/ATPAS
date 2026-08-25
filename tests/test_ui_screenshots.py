#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""UI screenshot smoke tests — render key widgets offscreen and verify pixels.

For every captured surface we assert that:
1. grab() succeeds and produces a non-empty pixmap.
2. The image is not a single flat colour (i.e. something actually rendered).

Captures are saved to output/ui_screenshots/ for manual inspection, and the
test prints the path. This catches rendering crashes and catastrophic layout
breakage (e.g. RTL regressions) without requiring a display.

Run:
    python -m pytest tests/test_ui_screenshots.py -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _get_or_create_app():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


@pytest.fixture(scope="module")
def qapp():
    return _get_or_create_app()


@pytest.fixture(scope="module")
def registry():
    from utils.json_manager import load_json
    return load_json("codes_registry.json")


@pytest.fixture(scope="module")
def config():
    from utils.json_manager import load_json
    return load_json("master_config.json")


@pytest.fixture(scope="module")
def presets():
    from utils.json_manager import load_json
    try:
        return load_json("presets.json")
    except FileNotFoundError:
        return {"presets": {}}


SCREENSHOT_DIR = Path("output") / "ui_screenshots"


def _grab_and_check(qapp, widget, name: str) -> Path:
    """Render widget offscreen, sanity-check pixels, save PNG, return path."""
    from PyQt5.QtCore import Qt

    widget.setLayoutDirection(Qt.RightToLeft)
    widget.resize(widget.sizeHint().expandedTo(widget.minimumSizeHint()))
    widget.show()
    qapp.processEvents()

    pix = widget.grab()
    assert not pix.isNull(), f"{name}: grab() returned a null pixmap"
    assert pix.width() > 50 and pix.height() > 50, (
        f"{name}: suspiciously small render {pix.width()}x{pix.height()}"
    )

    img = pix.toImage()
    # Flat-colour check: sample a grid; at least two distinct colours must exist.
    colours = set()
    step_x = max(1, img.width() // 8)
    step_y = max(1, img.height() // 8)
    for x in range(0, img.width(), step_x):
        for y in range(0, img.height(), step_y):
            colours.add(img.pixel(x, y))
            if len(colours) > 1:
                break
        if len(colours) > 1:
            break
    assert len(colours) > 1, f"{name}: rendered as a single flat colour"

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SCREENSHOT_DIR / f"{name}.png"
    pix.save(str(out_path), "PNG")

    widget.close()
    qapp.processEvents()
    return out_path


def test_screenshot_project_selector(qapp, config):
    from ui.project_selector import ProjectSelectorWidget
    w = ProjectSelectorWidget(config)
    path = _grab_and_check(qapp, w, "project_selector")
    assert path.exists()


def test_screenshot_checkbox_selector(qapp, registry, config, presets):
    from ui.checkbox_selector import CheckboxSelectorWidget
    pids = list(config.get("projects", {}).keys())[:1]
    owner = ""
    for pid in pids:
        owners = config.get("projects", {}).get(pid, {}).get("applicable_owners", [])
        if owners:
            owner = owners[0]
            break
    w = CheckboxSelectorWidget(registry)
    w.update_for_project(pids, owner, [])
    path = _grab_and_check(qapp, w, "checkbox_selector")
    assert path.exists()


def test_screenshot_preview_panel(qapp, registry, config):
    from ui.preview_panel import PreviewPanelWidget
    codes = list(registry.get("codes", {}))[:5]
    w = PreviewPanelWidget(registry.get("codes", {}))
    w.update_preview(codes, [], [])
    path = _grab_and_check(qapp, w, "preview_panel")
    assert path.exists()


def test_screenshot_header_widget(qapp, registry, config):
    from ui.header_widget import HeaderWidget
    w = HeaderWidget(active_codes=len(registry.get("codes", {})))
    path = _grab_and_check(qapp, w, "header_widget")
    assert path.exists()


def test_screenshot_help_dialog(qapp):
    from ui.help_dialog import HelpDialog
    dlg = HelpDialog(tab_index=0)
    path = _grab_and_check(qapp, dlg, "help_dialog")
    assert path.exists()


def test_screenshot_metric_card_component(qapp):
    from ui.components import MetricCard, SectionTitleLabel
    from PyQt5.QtWidgets import QWidget, QVBoxLayout

    host = QWidget()
    layout = QVBoxLayout(host)
    layout.addWidget(SectionTitleLabel("اختبار المكونات"))
    layout.addWidget(MetricCard("42", "كوداً نشطاً", "#2B7549"))
    path = _grab_and_check(qapp, host, "components_smoke")
    assert path.exists()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
