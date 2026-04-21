#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS main UI window — Sprint 3 (BKL-001 through BKL-006).

Integrates:
- ProjectSelectorWidget  (BKL-002): project + owner selection
- CheckboxSelectorWidget (BKL-003): filtered, grouped code checkboxes
- PreviewPanelWidget     (BKL-004): sorted preview, validation messages, build button
- BuildProgressDialog    (BKL-005): QThread worker + progress dialog
- Builder engine         (BKL-006): full validator→resolver→builder→style_applier pipeline

Signal flow:
  project_selector.selection_changed(pid, oid)
      → _on_selection_changed → checkbox_selector.update_for_project(pid, oid, mandatory)
  checkbox_selector.codes_changed(code_ids)
      → _on_codes_changed → Validator.validate → preview_panel.update_preview
  preview_panel.auto_fix_requested
      → _on_auto_fix → DependencyResolver.suggest_missing → checkbox_selector.add_codes
  preview_panel.build_requested
      → _on_build_requested → BuildProgressDialog (runs Builder in QThread)
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from engine.dependency_resolver import DependencyResolver
from engine.error_handler import arabic_message
from engine.logger import setup_logging
from engine.validator import Validator
from ui.build_progress import BuildProgressDialog
from ui.checkbox_selector import CheckboxSelectorWidget
from ui.header_widget import HeaderWidget
from ui.preview_panel import PreviewPanelWidget
from ui.presets_panel import PresetsPanelWidget
from ui.project_selector import ProjectSelectorWidget
from ui.motion import motion_ms, motion_single_shot, prefers_reduced_motion
from utils.json_manager import load_json

def _get_output_dir() -> Path:
    """Return the output directory — next to EXE when frozen, else local."""
    if getattr(__import__("sys"), "frozen", False):
        import sys as _sys
        return Path(_sys.executable).parent / "output" / "generated_documents"
    return Path("output/generated_documents")


def _safe_int(value: Any, default: int) -> int:
    """Parse int safely; fallback to default on malformed config values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

_DEFAULT_WINDOW_TITLE_AR = "نظام بناء العروض الفنية - الرواف"

# Rotating status bar tips — shown every ~10 s during idle
_STATUS_TIPS: list[str] = [
    "💡 اختر «الكل» في أي تصنيف للتحديد الجماعي",
    "⚡ الأنماط الجاهزة توفّر 80% من وقت الاختيار",
    "📋 التبعيات الهندسية تُحلّ تلقائياً — العرض دائماً مكتمل",
    "🔍 ابحث بالاسم أو رقم الكود في خانة البحث",
    "📄 الملف الناتج .docx متوافق مع جميع إصدارات Word",
    "🏗️ يدعم 6 أنواع مشاريع و9 جهات مالكة في منطقة الرياض",
    "📁 استخدم زر «فتح المجلد» لتحديد الملف مباشرةً في Explorer",
]


class MainWindow(QMainWindow):
    """Main shell window for ATPAS desktop UI."""

    def __init__(
        self,
        registry_path: str | Path = "codes_registry.json",
        config_path: str | Path = "master_config.json",
    ) -> None:
        super().__init__()
        setup_logging()
        self._logger = logging.getLogger(__name__)

        self._registry_path = Path(registry_path)
        self._config_path = Path(config_path)
        self._presets_path = Path("presets.json")

        self.registry_data: dict[str, Any] = {}
        self.config_data: dict[str, Any] = {}
        self.presets_data: dict[str, Any] = {}
        self._startup_errors: list[str] = []

        # Engine objects (built after data loads)
        self._validator: Validator | None = None
        self._resolver: DependencyResolver | None = None

        # UI widgets (set in _build_layout)
        self._header: HeaderWidget | None = None
        self._project_selector: ProjectSelectorWidget | None = None
        self._checkbox_selector: CheckboxSelectorWidget | None = None
        self._preview_panel: PreviewPanelWidget | None = None
        self._presets_panel: PresetsPanelWidget | None = None
        self._startup_anim_started = False
        self._entry_anims: list[QPropertyAnimation] = []
        self._status_hold_until = 0.0
        self._focus_search_action: QAction | None = None

        self._load_startup_data()
        self._build_engine()
        self._configure_window()
        self._build_layout()
        self._show_startup_issues_if_any()

    def showEvent(self, event) -> None:  # type: ignore[override]
        """Play one-time entry choreography after first paint."""
        super().showEvent(event)
        if self._startup_anim_started:
            return
        self._startup_anim_started = True
        motion_single_shot(50, self._play_startup_choreography)

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def _load_startup_data(self) -> None:
        self._load_config()
        self._load_registry()
        self._load_presets()

    def _load_config(self) -> None:
        try:
            self.config_data = load_json(self._config_path)
        except Exception as exc:  # noqa: BLE001
            self.config_data = {}
            ar = arabic_message(exc)
            self._startup_errors.append(f"{ar}: {self._config_path}")
            self._logger.exception("Failed loading config from %s", self._config_path)

    def _load_registry(self) -> None:
        try:
            self.registry_data = load_json(self._registry_path)
            if not isinstance(self.registry_data.get("codes"), dict):
                raise ValueError("الحقل codes غير موجود أو غير صحيح")
        except Exception as exc:  # noqa: BLE001
            self.registry_data = {"codes": {}}
            ar = arabic_message(exc)
            self._startup_errors.append(f"{ar}: {self._registry_path}")
            self._logger.exception("Failed loading registry from %s", self._registry_path)

    def _load_presets(self) -> None:
        try:
            self.presets_data = load_json(self._presets_path)
        except Exception as exc:  # noqa: BLE001
            self.presets_data = {"presets": {}}
            self._logger.warning("presets.json not found or invalid: %s", exc)

    def _build_engine(self) -> None:
        codes = self.registry_data.get("codes", {})
        self._validator = Validator(codes)
        self._resolver = DependencyResolver(codes)

    # ------------------------------------------------------------------
    # Window layout
    # ------------------------------------------------------------------

    def _configure_window(self) -> None:
        ui_cfg = self.config_data.get("ui_config", {})
        title = ui_cfg.get("window_title") or _DEFAULT_WINDOW_TITLE_AR
        width = max(_safe_int(ui_cfg.get("window_width"), 1280), 960)
        height = max(_safe_int(ui_cfg.get("window_height"), 860), 640)

        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(960, 640)
        self.setLayoutDirection(Qt.RightToLeft)

        self.setStatusBar(QStatusBar(self))
        self._active_count = sum(
            1
            for c in self.registry_data.get("codes", {}).values()
            if c.get("status") == "active"
        )
        self._show_status(
            f"تم تحميل {self._active_count} كود نشط — اختر المشروع للبدء",
            hold_ms=15_000,
        )

        # Rotating tips — start after 15 s so the user can read the initial message
        self._tip_index = 0
        self._tips_timer = QTimer(self)
        self._tips_timer.setInterval(10_000)   # rotate every 10 s
        self._tips_timer.timeout.connect(self._show_next_tip)
        QTimer.singleShot(15_000, self._tips_timer.start)

    def _build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Branded header ─────────────────────────────────────────────
        self._header = HeaderWidget(
            active_codes=getattr(self, "_active_count", 0), parent=self
        )
        root_layout.addWidget(self._header)

        # ── Content area (with margins) ────────────────────────────────
        content = QWidget()
        content.setLayoutDirection(Qt.RightToLeft)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 10, 12, 10)
        content_layout.setSpacing(8)
        root_layout.addWidget(content, stretch=1)

        # Redirect all subsequent widget additions to content_layout
        root_layout = content_layout   # shadow the outer var for the rest of this method

        # ── Top row: project + owner selector ──────────────────────────
        self._project_selector = ProjectSelectorWidget(self.config_data, parent=self)
        root_layout.addWidget(self._project_selector)

        # ── Presets strip ──────────────────────────────────────────────
        self._presets_panel = PresetsPanelWidget(self.presets_data, parent=self)
        root_layout.addWidget(self._presets_panel)

        # ── Middle: codes checkboxes (left) + preview (right) ──────────
        middle = QHBoxLayout()
        root_layout.addLayout(middle, stretch=1)

        self._checkbox_selector = CheckboxSelectorWidget(self.registry_data, parent=self)
        middle.addWidget(self._checkbox_selector, stretch=3)

        self._preview_panel = PreviewPanelWidget(self.registry_data, parent=self)
        middle.addWidget(self._preview_panel, stretch=2)

        # ── Wire signals ───────────────────────────────────────────────
        self._project_selector.selection_changed.connect(self._on_selection_changed)
        self._checkbox_selector.codes_changed.connect(self._on_codes_changed)
        self._preview_panel.auto_fix_requested.connect(self._on_auto_fix)
        self._preview_panel.build_requested.connect(self._on_build_requested)
        self._presets_panel.preset_applied.connect(self._on_preset_applied)
        self._wire_shortcuts()

        # Trigger initial load using whichever project/owner is pre-selected
        pids = self._project_selector.current_project_ids()
        oid = self._project_selector.current_owner_id()
        if pids and oid:
            self._on_selection_changed(pids, oid)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_selection_changed(self, project_ids: list[str], owner_id: str) -> None:
        """Rebuild checkbox list whenever project selection or owner changes."""
        mandatory = self._get_mandatory_codes(owner_id)
        self._checkbox_selector.update_for_project(project_ids, owner_id, mandatory)
        self._preview_panel.clear()
        projects_label = " + ".join(project_ids)
        self._show_status(
            f"المشاريع: {projects_label}  |  الجهة: {owner_id}  |  اختر الأكواد المطلوبة",
            hold_ms=5_000,
        )

    def _on_codes_changed(self, selected_codes: list[str]) -> None:
        """Run validator and refresh preview whenever checkbox state changes."""
        if not selected_codes:
            self._preview_panel.clear()
            return

        pids = self._project_selector.current_project_ids()
        oid = self._project_selector.current_owner_id()
        _valid, errors, warnings = self._validator.validate(selected_codes, oid, pids)
        self._preview_panel.update_preview(selected_codes, errors, warnings)

        count = len(selected_codes)
        err_count = len(errors)

        # Easter egg: acknowledge large proposals with a fitting message
        if count >= 20:
            status = f"🏗️ مشروع شامل — {count} كود" + (
                f"  |  {err_count} خطأ" if err_count else "  ✓ جاهز للبناء"
            )
        else:
            status = (
                f"{count} كود مختار"
                + (f"  |  {err_count} خطأ" if err_count else "  |  لا أخطاء")
            )
        self._show_status(status, timeout_ms=8_000)

    def _on_auto_fix(self) -> None:
        """Add all missing dependency codes to the checkbox selection."""
        current = self._checkbox_selector.get_selected_codes()
        missing = self._resolver.suggest_missing(current)
        if missing:
            self._checkbox_selector.add_codes(missing)
            self._show_status(
                f"تم إضافة {len(missing)} كود ناقص تلقائياً: {', '.join(missing)}",
                hold_ms=7_000,
            )
        else:
            self._show_status("لا توجد أكواد ناقصة — التبعيات مكتملة", hold_ms=5_000)

    def _on_preset_applied(
        self, project_ids: list[str], owner_id: str, code_ids: list[str]
    ) -> None:
        """Apply a preset: set project+owner (fires selection_changed → rebuild),
        then tick all preset codes on the freshly rebuilt checkbox list.
        """
        if not project_ids or not owner_id:
            self._show_status("الـ Preset غير مكتمل — لا يوجد مشروع أو جهة", hold_ms=4_000)
            return

        # apply_preset sets checkboxes + owner combo; their signals fire
        # selection_changed → _on_selection_changed → update_for_project (all synchronous).
        self._project_selector.apply_preset(project_ids, owner_id)

        # By now the checkbox list is rebuilt with only mandatory codes ticked.
        # Tick all preset codes on top of that.
        self._checkbox_selector.add_codes(code_ids)

        proj_label = " + ".join(project_ids)
        self._show_status(
            f"✅ تم تطبيق الـ Preset — المشروع: {proj_label} | "
            f"الجهة: {owner_id} | {len(code_ids)} كود مُختار",
            hold_ms=7_000,
        )

    def _on_build_requested(self) -> None:
        """BKL-006: Launch BuildProgressDialog with QThread builder (BKL-005)."""
        selected = self._checkbox_selector.get_selected_codes()
        if not selected:
            QMessageBox.warning(self, "تحذير", "لم يتم اختيار أي كود.")
            return

        pids = self._project_selector.current_project_ids()
        if not pids:
            QMessageBox.warning(self, "تحذير", "اختر مشروعاً واحداً على الأقل قبل البناء.")
            return
        pid = pids[0]
        oid = self._project_selector.current_owner_id()
        if not oid:
            QMessageBox.warning(self, "تحذير", "اختر جهة مالكة صالحة قبل البناء.")
            return

        output_dir = _get_output_dir()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "خطأ", f"تعذّر إنشاء مجلد المخرجات:\n{exc}")
            return

        dialog = BuildProgressDialog(
            codes=self.registry_data.get("codes", {}),
            selected_codes=selected,
            project_id=pid,
            owner_id=oid,
            output_dir=output_dir,
            parent=self,
        )
        dialog.start_build()
        dialog.exec_()

    def _show_next_tip(self) -> None:
        """Rotate through status bar tips during idle periods."""
        if time.monotonic() < self._status_hold_until:
            return
        tip = _STATUS_TIPS[self._tip_index % len(_STATUS_TIPS)]
        self._show_status(tip, timeout_ms=9_000, hold_ms=0)
        self._tip_index += 1

    def _play_startup_choreography(self) -> None:
        """Staggered panel fade-in for a focused first impression."""
        if prefers_reduced_motion():
            return

        targets = [
            self._project_selector,
            self._presets_panel,
            self._checkbox_selector,
            self._preview_panel,
        ]
        self._entry_anims.clear()

        for i, widget in enumerate(targets):
            if widget is None:
                continue
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", widget)
            anim.setDuration(motion_ms(420))
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            self._entry_anims.append(anim)

            def _cleanup(w=widget, a=anim) -> None:
                w.setGraphicsEffect(None)
                if a in self._entry_anims:
                    self._entry_anims.remove(a)

            anim.finished.connect(_cleanup)
            motion_single_shot(110 * i, lambda a=anim: a.start())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _wire_shortcuts(self) -> None:
        """Register global shortcuts for high-frequency actions."""
        self._focus_search_action = QAction(self)
        self._focus_search_action.setShortcut(QKeySequence("Ctrl+F"))
        self._focus_search_action.setShortcutContext(Qt.WindowShortcut)
        self._focus_search_action.triggered.connect(self._focus_code_search)
        self.addAction(self._focus_search_action)

    def _focus_code_search(self) -> None:
        """Focus code search box from anywhere in the main window."""
        if self._checkbox_selector is not None:
            self._checkbox_selector.focus_search()

    def _show_status(
        self,
        message: str,
        timeout_ms: int = 0,
        hold_ms: int | None = None,
    ) -> None:
        """Show status text and optionally block rotating tips for a short period."""
        self.statusBar().showMessage(message, timeout_ms)
        if hold_ms is None:
            hold_ms = timeout_ms
        if hold_ms > 0:
            self._status_hold_until = max(
                self._status_hold_until,
                time.monotonic() + hold_ms / 1000.0,
            )

    def _get_mandatory_codes(self, owner_id: str) -> list[str]:
        """Read mandatory_codes from owner_specifications in config_data."""
        owner_specs = self.config_data.get("owner_specifications", {})
        return list(owner_specs.get(owner_id, {}).get("mandatory_codes", []))

    def _show_startup_issues_if_any(self) -> None:
        if not self._startup_errors:
            return
        details = "\n".join(f"• {item}" for item in self._startup_errors)
        QMessageBox.warning(
            self,
            "تنبيه عند بدء التشغيل",
            "تم فتح الواجهة مع وجود مشاكل في التحميل:\n\n" + details,
        )


def launch_main_window(
    registry_path: str | Path = "codes_registry.json",
    config_path: str | Path = "master_config.json",
) -> int:
    """Standalone launcher for manual GUI testing."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(registry_path=registry_path, config_path=config_path)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(launch_main_window())
