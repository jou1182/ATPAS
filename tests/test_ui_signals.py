#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""UI signal/slot integration tests (headless, no display required).

Uses pytest-qt (or a minimal QApplication fixture) to verify that:
• Widget signals are defined and emit with the correct signatures.
• Signal → slot connections behave as expected (no crashes, correct data).
• State machines (enabled/disabled buttons) transition correctly.

All tests run without a visible window — safe for CI environments.

Run from the project root:
    python -m pytest tests/test_ui_signals.py -v
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

import pytest

# --------------------------------------------------------------------------
# Minimal QApplication bootstrap (idempotent — safe if already created)
# --------------------------------------------------------------------------

def _get_or_create_app():
    """Return the existing QApplication or create a headless one."""
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


# --------------------------------------------------------------------------
# PreviewPanelWidget signal tests
# --------------------------------------------------------------------------

class TestPreviewPanelSignals:
    """Verify PreviewPanelWidget emits correct signals."""

    def test_build_requested_signal_exists(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        assert hasattr(widget, "build_requested")

    def test_auto_fix_requested_signal_exists(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        assert hasattr(widget, "auto_fix_requested")

    def test_build_btn_disabled_initially(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        assert not widget._build_btn.isEnabled()

    def test_export_btn_disabled_initially(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        assert not widget._export_btn.isEnabled()
        assert not widget._outline_btn.isEnabled()

    def test_update_preview_enables_export_btn(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:3]
        widget.update_preview(codes, [], [])
        assert widget._export_btn.isEnabled()
        assert widget._outline_btn.isEnabled()

    def test_update_preview_enables_build_btn_when_no_errors(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:2]
        widget.update_preview(codes, errors=[], warnings=[])
        assert widget._build_btn.isEnabled()

    def test_update_preview_disables_build_btn_when_errors(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:2]
        widget.update_preview(codes, errors=["خطأ ما"], warnings=[])
        assert not widget._build_btn.isEnabled()

    def test_clear_disables_all_buttons(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:2]
        widget.update_preview(codes, [], [])
        widget.clear()
        assert not widget._build_btn.isEnabled()
        assert not widget._export_btn.isEnabled()
        assert not widget._outline_btn.isEnabled()

    def test_build_requested_emitted_on_click(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:2]
        widget.update_preview(codes, [], [])

        received: list[bool] = []
        widget.build_requested.connect(lambda: received.append(True))
        widget._build_btn.click()
        assert received == [True]

    def test_auto_fix_emitted_on_click(self, qapp, registry) -> None:
        from ui.preview_panel import PreviewPanelWidget
        widget = PreviewPanelWidget(registry)
        codes = list(registry["codes"].keys())[:2]
        widget.update_preview(codes, errors=[], warnings=["تحذير"])

        received: list[bool] = []
        widget.auto_fix_requested.connect(lambda: received.append(True))
        widget._autofix_btn.click()
        assert received == [True]


# --------------------------------------------------------------------------
# PresetsPanelWidget signal tests
# --------------------------------------------------------------------------

class TestPresetsPanelSignals:
    """Verify PresetsPanelWidget signals are defined and wired."""

    def test_preset_applied_signal_exists(self, qapp, presets) -> None:
        from ui.presets_panel import PresetsPanelWidget
        widget = PresetsPanelWidget(presets)
        assert hasattr(widget, "preset_applied")

    def test_save_requested_signal_exists(self, qapp, presets) -> None:
        from ui.presets_panel import PresetsPanelWidget
        widget = PresetsPanelWidget(presets)
        assert hasattr(widget, "save_requested")

    def test_history_requested_signal_exists(self, qapp, presets) -> None:
        from ui.presets_panel import PresetsPanelWidget
        widget = PresetsPanelWidget(presets)
        assert hasattr(widget, "history_requested")

    def test_toggle_panel_collapses_and_expands(self, qapp, presets) -> None:
        from ui.presets_panel import PresetsPanelWidget
        widget = PresetsPanelWidget(presets)
        assert widget._expanded is True
        widget._toggle_panel()
        assert widget._expanded is False
        widget._toggle_panel()
        assert widget._expanded is True

    def test_refresh_does_not_crash_on_empty_presets(self, qapp) -> None:
        from ui.presets_panel import PresetsPanelWidget
        widget = PresetsPanelWidget({"presets": {}})
        widget.refresh({"presets": {}})   # must not raise


# --------------------------------------------------------------------------
# HeaderWidget signal tests
# --------------------------------------------------------------------------

class TestHeaderWidgetSignals:
    """Verify HeaderWidget signals exist and emit."""

    def test_help_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "help_requested")

    def test_import_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "import_requested")

    def test_backup_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "backup_requested")

    def test_health_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "health_requested")

    def test_code_manager_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "code_manager_requested")

    def test_last_proposal_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "last_proposal_requested")

    def test_about_requested_signal_exists(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=10)
        assert hasattr(widget, "about_requested")

    def test_update_counter_does_not_crash(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=0)
        widget.update_counter(64)   # must not raise

    def test_update_counter_to_zero(self, qapp) -> None:
        from ui.header_widget import HeaderWidget
        widget = HeaderWidget(active_codes=64)
        widget.update_counter(0)    # must not raise


# --------------------------------------------------------------------------
# SessionHistoryDialog smoke tests
# --------------------------------------------------------------------------

class TestSessionHistoryDialog:
    """Session history dialog should open safely with/without saved sessions."""

    def test_empty_sessions_dialog_does_not_crash(self, qapp, monkeypatch) -> None:
        monkeypatch.setattr("ui.session_history_dialog.get_sessions", lambda: [])

        from ui.session_history_dialog import SessionHistoryDialog

        dialog = SessionHistoryDialog()
        assert dialog._list.count() == 1
        assert not dialog._restore_btn.isEnabled()
        assert not dialog._delete_btn.isEnabled()

    def test_sessions_dialog_populates_saved_session(self, qapp, monkeypatch) -> None:
        monkeypatch.setattr("ui.session_history_dialog.get_sessions", lambda: [{
            "project_ids": ["wastewater"],
            "owner_id": "nwc",
            "selected_codes": ["001-SUR-BASE"],
            "timestamp": 1_700_000_000,
            "code_count": 1,
            "page_count": 2,
        }])

        from ui.session_history_dialog import SessionHistoryDialog

        dialog = SessionHistoryDialog()
        assert dialog._list.count() == 1
        dialog._list.setCurrentRow(0)
        assert dialog._restore_btn.isEnabled()
        assert dialog._delete_btn.isEnabled()


# --------------------------------------------------------------------------
# CheckboxSelectorWidget cache and interaction tests
# --------------------------------------------------------------------------

class TestCheckboxSelectorWidget:
    """Verify code-list caching stays safe across project switches."""

    def test_project_container_cache_reuses_existing_widgets(self, qapp, registry, config) -> None:
        from ui.checkbox_selector import CheckboxSelectorWidget

        widget = CheckboxSelectorWidget(registry)
        mandatory = config["owner_specifications"]["nwc"].get("mandatory_codes", [])

        widget.update_for_project(["wastewater"], "nwc", mandatory)
        first_container = widget._current_container
        assert first_container is not None
        assert widget._cache_key(["wastewater"], "nwc") in widget._container_cache

        widget.update_for_project(["water_supply"], "nwc", mandatory)
        widget.update_for_project(["wastewater"], "nwc", mandatory)

        assert widget._current_container is first_container

    def test_code_item_flash_does_not_raise(self, qapp, registry, config) -> None:
        from ui.checkbox_selector import CheckboxSelectorWidget

        widget = CheckboxSelectorWidget(registry)
        mandatory = config["owner_specifications"]["nwc"].get("mandatory_codes", [])
        widget.update_for_project(["wastewater"], "nwc", mandatory)

        first_item = next(iter(widget._checkboxes.values()))
        first_item._flash_row(2)


# --------------------------------------------------------------------------
# BuildHistoryManager tests
# --------------------------------------------------------------------------

class TestBuildHistoryManager:
    """Verify BuildHistoryManager persistence without QApplication."""

    def test_save_and_load_entry(self, tmp_path: Path) -> None:
        from ui.build_history import BuildHistoryManager
        mgr = BuildHistoryManager(history_path=tmp_path / "history.json")
        mgr.save_entry(
            project_id="wastewater",
            owner_id="nwc",
            codes=["001-SUR-BASE", "002-EXC-FINE"],
            output_file="/output/test.docx",
            elapsed_seconds=3.5,
            page_count=12,
        )
        entries = mgr.load()
        assert len(entries) == 1
        assert entries[0]["project_id"] == "wastewater"
        assert entries[0]["owner_id"] == "nwc"
        assert entries[0]["page_count"] == 12

    def test_history_capped_at_fifty_entries(self, tmp_path: Path) -> None:
        from ui.build_history import BuildHistoryManager
        mgr = BuildHistoryManager(history_path=tmp_path / "history.json")
        for i in range(55):
            mgr.save_entry(
                project_id=f"proj_{i}",
                owner_id="nwc",
                codes=["001-SUR-BASE"],
                output_file=f"/output/{i}.docx",
                elapsed_seconds=1.0,
                page_count=i,
            )
        entries = mgr.load()
        assert len(entries) == 50, f"Expected 50 entries, got {len(entries)}"

    def test_newest_entry_is_first(self, tmp_path: Path) -> None:
        from ui.build_history import BuildHistoryManager
        mgr = BuildHistoryManager(history_path=tmp_path / "history.json")
        for label in ["first", "second", "third"]:
            mgr.save_entry(
                project_id=label,
                owner_id="nwc",
                codes=[],
                output_file="",
                elapsed_seconds=0.0,
                page_count=0,
            )
        entries = mgr.load()
        assert entries[0]["project_id"] == "third"

    def test_load_returns_empty_list_when_no_file(self, tmp_path: Path) -> None:
        from ui.build_history import BuildHistoryManager
        mgr = BuildHistoryManager(history_path=tmp_path / "nonexistent.json")
        assert mgr.load() == []


# --------------------------------------------------------------------------
# BackupManager functional tests
# --------------------------------------------------------------------------

class TestBackupManager:
    """Verify create_backup / list_backups without UI."""

    def test_create_backup_returns_zip_path(self, tmp_path: Path, monkeypatch) -> None:
        import ui.backup_manager as bm
        monkeypatch.setattr(bm, "_BACKUP_DIR", tmp_path / "backups")
        path = bm.create_backup("test")
        assert path.exists()
        assert path.suffix == ".zip"

    def test_backup_contains_registry(self, tmp_path: Path, monkeypatch) -> None:
        import zipfile
        import ui.backup_manager as bm
        monkeypatch.setattr(bm, "_BACKUP_DIR", tmp_path / "backups")
        path = bm.create_backup()
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        assert "codes_registry.json" in names

    def test_list_backups_sorted_newest_first(self, tmp_path: Path, monkeypatch) -> None:
        import time
        import ui.backup_manager as bm
        monkeypatch.setattr(bm, "_BACKUP_DIR", tmp_path / "backups")
        b1 = bm.create_backup("first")
        time.sleep(0.05)
        b2 = bm.create_backup("second")
        listing = bm.list_backups()
        assert listing[0] == b2   # newest first
        assert listing[1] == b1

    def test_list_backups_empty_when_no_dir(self, tmp_path: Path, monkeypatch) -> None:
        import ui.backup_manager as bm
        monkeypatch.setattr(bm, "_BACKUP_DIR", tmp_path / "does_not_exist")
        assert bm.list_backups() == []


class TestHeaderWidgetButtons:
    """Header factory buttons: every table row wires its signal correctly."""

    def test_all_header_signals_defined(self, qapp) -> None:
        from ui.header_widget import HeaderWidget, _HEADER_BUTTONS
        w = HeaderWidget(active_codes=5)
        for signal_name, _label, _tip, _accent in _HEADER_BUTTONS:
            assert hasattr(w, signal_name), f"missing signal {signal_name}"

    def test_button_click_emits_signal(self, qapp) -> None:
        from PyQt5.QtWidgets import QPushButton

        from ui.header_widget import HeaderWidget
        w = HeaderWidget(active_codes=0)
        received: list[str] = []
        w.help_requested.connect(lambda: received.append("help"))
        w.settings_requested.connect(lambda: received.append("settings"))
        buttons = {b.text(): b for b in w.findChildren(QPushButton)}
        help_btn = next(b for text, b in buttons.items() if "مساعدة" in text)
        settings_btn = next(b for text, b in buttons.items() if "إعدادات" in text)
        help_btn.clicked.emit(True)
        settings_btn.clicked.emit(False)
        assert received == ["help", "settings"], f"got {received}"
