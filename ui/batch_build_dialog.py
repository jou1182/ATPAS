#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء متعدد المشاريع — Batch Build Dialog.

Multi-step dialog:
  Step 1 (Job List screen)  — add, edit, remove jobs; each job comes from a preset
                               or is configured manually.
  Step 2 (Progress screen)  — runs BatchRunner in a QThread and shows live status.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from utils.batch_runner import BatchJob, BatchJobResult, BatchRunner
from utils.json_manager import load_json

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# QThread wrapper
# ─────────────────────────────────────────────────────────────────────────────

class BatchThread(QThread):
    """Runs BatchRunner.run() off the UI thread."""

    job_started = pyqtSignal(int, int, str)    # index, total, job_id
    job_done    = pyqtSignal(object)           # BatchJobResult (object to skip Qt registration)
    all_done    = pyqtSignal(list)             # list[BatchJobResult]

    def __init__(self, runner: BatchRunner, jobs: list[BatchJob], parent=None) -> None:
        super().__init__(parent)
        self._runner = runner
        self._jobs = jobs

    def run(self) -> None:
        self._runner.run(
            self._jobs,
            on_job_start=lambda idx, total, jid: self.job_started.emit(idx, total, jid),
            on_job_done=lambda result: self.job_done.emit(result),
            on_all_done=lambda results: self.all_done.emit(results),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Preset picker sub-dialog
# ─────────────────────────────────────────────────────────────────────────────

class _PresetPickerDialog(QDialog):
    """Small dialog that lets the user pick one preset from presets.json."""

    def __init__(self, presets_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("اختر نمطاً جاهزاً")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(460)
        self.setModal(True)

        self._selected_preset_id: str | None = None
        self._selected_preset_data: dict | None = None

        presets_raw = load_json(presets_path, default={"presets": {}})
        self._presets: dict[str, dict] = presets_raw.get("presets", {})

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        lbl = QLabel("الأنماط الجاهزة المتاحة:")
        lbl.setStyleSheet("font-weight: 700; font-size: 13px;")
        layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setLayoutDirection(Qt.RightToLeft)
        self._list.setMinimumHeight(280)
        for pid, pdata in self._presets.items():
            name = pdata.get("name_ar", pid)
            icon = pdata.get("icon", "")
            codes = pdata.get("codes", [])
            owner = pdata.get("owner_id", "")
            label = f"{icon} {name}  ({len(codes)} كود)  — {owner}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, pid)
            self._list.addItem(item)
        layout.addWidget(self._list)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("إضافة")
        btns.button(QDialogButtonBox.Cancel).setText("إلغاء")
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self._list.doubleClicked.connect(lambda _: self._on_accept())

    def _on_accept(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر نمطاً جاهزاً أولاً.")
            return
        item = self._list.item(row)
        pid = item.data(Qt.UserRole)
        self._selected_preset_id = pid
        self._selected_preset_data = self._presets[pid]
        self.accept()

    def selected_preset(self) -> tuple[str, dict] | None:
        if self._selected_preset_id and self._selected_preset_data:
            return self._selected_preset_id, self._selected_preset_data
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Job list screen (Step 1)
# ─────────────────────────────────────────────────────────────────────────────

_STYLE_PRIMARY = (
    "QPushButton {"
    f"  background: {theme.HEADER}; color: {theme.ACCENT};"
    "  border: none; border-radius: 6px;"
    "  padding: 7px 18px; font-size: 12px; font-weight: 700;"
    "}"
    f"QPushButton:hover {{ background: {theme.NAVY_MID}; }}"
    f"QPushButton:pressed {{ background: {theme.HEADER2}; }}"
    "QPushButton:disabled { background: #BDBDBD; color: #757575; }"
)

_STYLE_SECONDARY = (
    "QPushButton {"
    f"  background: {theme.SURFACE}; color: {theme.HEADER};"
    f"  border: 1.5px solid {theme.HEADER}; border-radius: 6px;"
    "  padding: 6px 16px; font-size: 12px; font-weight: 700;"
    "}"
    f"QPushButton:hover {{ background: {theme.BG}; }}"
    f"QPushButton:pressed {{ background: {theme.BORDER}; }}"
    "QPushButton:disabled { color: #BDBDBD; border-color: #BDBDBD; }"
)

_STYLE_DANGER = (
    "QPushButton {"
    "  background: #B71C1C; color: #FFFFFF;"
    "  border: none; border-radius: 5px;"
    "  padding: 4px 10px; font-size: 11px;"
    "}"
    "QPushButton:hover { background: #D32F2F; }"
    "QPushButton:pressed { background: #7F0000; }"
)


class _JobListScreen(QWidget):
    """Step 1: shows the list of queued jobs and controls to add/remove them."""

    build_requested = pyqtSignal(list)  # list[BatchJob]

    def __init__(self, presets_path: Path, output_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._presets_path = presets_path
        self._output_dir = output_dir
        self._jobs: list[BatchJob] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        hdr = QLabel("الوظائف المُضافة:")
        hdr.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {theme.HEADER};")
        layout.addWidget(hdr)

        # Job list
        self._list_widget = QListWidget()
        self._list_widget.setLayoutDirection(Qt.RightToLeft)
        self._list_widget.setMinimumHeight(220)
        self._list_widget.setStyleSheet(
            "QListWidget {"
            "  border: 1px solid #C0CBDA; border-radius: 6px;"
            "  background: #F8FAFC; font-size: 12px;"
            "}"
            "QListWidget::item { padding: 6px 10px; border-bottom: 1px solid #E8EDF2; }"
            f"QListWidget::item:selected {{ background: #EBF5FB; color: {theme.HEADER}; }}"
        )
        layout.addWidget(self._list_widget, stretch=1)

        # Empty hint
        self._empty_lbl = QLabel("لا توجد وظائف بعد — أضف وظيفة من نمط جاهز أدناه")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #8A9BB0; font-size: 12px; margin: 4px;")
        layout.addWidget(self._empty_lbl)

        # Per-item controls (delete selected)
        item_row = QHBoxLayout()
        self._del_btn = QPushButton("✗ حذف المحدد")
        self._del_btn.setStyleSheet(_STYLE_DANGER)
        self._del_btn.setEnabled(False)
        self._del_btn.clicked.connect(self._delete_selected)
        item_row.addStretch()
        item_row.addWidget(self._del_btn)
        layout.addLayout(item_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #C0CBDA;")
        layout.addWidget(sep)

        # Add-job buttons
        add_row = QHBoxLayout()
        add_preset_btn = QPushButton("+ إضافة وظيفة من نمط جاهز")
        add_preset_btn.setStyleSheet(_STYLE_SECONDARY)
        add_preset_btn.clicked.connect(self._add_from_preset)
        add_row.addWidget(add_preset_btn)
        add_row.addStretch()
        layout.addLayout(add_row)

        # Build / cancel row
        bottom_row = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(_STYLE_SECONDARY)
        cancel_btn.clicked.connect(self._on_cancel)
        self._build_btn = QPushButton("▶ بناء الكل")
        self._build_btn.setStyleSheet(_STYLE_PRIMARY)
        self._build_btn.setEnabled(False)
        self._build_btn.clicked.connect(self._on_build)
        bottom_row.addWidget(cancel_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self._build_btn)
        layout.addLayout(bottom_row)

        # Wire list selection
        self._list_widget.currentRowChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------

    def _on_selection_changed(self, row: int) -> None:
        self._del_btn.setEnabled(row >= 0)

    def _update_list_display(self) -> None:
        self._list_widget.clear()
        for i, job in enumerate(self._jobs):
            label = (
                f"#{i + 1}  {job.project_id} — {job.owner_id}"
                f"  |  {len(job.selected_codes)} كود"
                f"  |  {job.job_id}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, i)
            self._list_widget.addItem(item)

        has_jobs = bool(self._jobs)
        self._empty_lbl.setVisible(not has_jobs)
        self._list_widget.setVisible(has_jobs)
        self._build_btn.setEnabled(has_jobs)
        self._del_btn.setEnabled(False)

    def _add_from_preset(self) -> None:
        picker = _PresetPickerDialog(self._presets_path, parent=self)
        if picker.exec_() != QDialog.Accepted:
            return
        result = picker.selected_preset()
        if not result:
            return
        _pid, pdata = result
        project_ids: list[str] = pdata.get("project_ids", [])
        owner_id: str = pdata.get("owner_id", "")
        codes: list[str] = pdata.get("codes", [])
        if not project_ids or not owner_id or not codes:
            QMessageBox.warning(self, "بيانات ناقصة", "النمط الجاهز لا يحتوي على بيانات كافية.")
            return

        job_index = len(self._jobs) + 1
        job_id = f"job_{job_index:03d}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            self._output_dir
            / f"batch_{project_ids[0]}_{owner_id}_{timestamp}_{job_index:02d}.docx"
        )
        job = BatchJob(
            job_id=job_id,
            project_id=project_ids[0],
            owner_id=owner_id,
            selected_codes=codes,
            output_path=output_path,
        )
        self._jobs.append(job)
        self._update_list_display()

    def _delete_selected(self) -> None:
        row = self._list_widget.currentRow()
        if row < 0 or row >= len(self._jobs):
            return
        del self._jobs[row]
        # Re-number job IDs for display consistency
        for i, job in enumerate(self._jobs):
            job.job_id = f"job_{i + 1:03d}"
        self._update_list_display()

    def _on_build(self) -> None:
        if not self._jobs:
            QMessageBox.warning(self, "تنبيه", "أضف وظيفة واحدة على الأقل قبل البناء.")
            return
        self.build_requested.emit(list(self._jobs))

    def _on_cancel(self) -> None:
        # Walk up to the QDialog and reject it
        p = self.parent()
        while p and not isinstance(p, QDialog):
            p = p.parent()
        if p:
            p.reject()

    def get_jobs(self) -> list[BatchJob]:
        return list(self._jobs)


# ─────────────────────────────────────────────────────────────────────────────
# Progress screen (Step 2)
# ─────────────────────────────────────────────────────────────────────────────

_STATUS_ICONS = {
    "pending": "⏳ قيد الانتظار",
    "running": "🔄 جارٍ البناء...",
    "done_ok": "✅ تم",
    "done_err": "✗ فشل",
}


class _ProgressScreen(QWidget):
    """Step 2: runs jobs via BatchThread and updates the list in real-time."""

    all_done = pyqtSignal(list)  # list[BatchJobResult]

    def __init__(self, codes: dict, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._codes = codes
        self._thread: BatchThread | None = None
        self._items: list[QListWidgetItem] = []
        self._total = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        hdr = QLabel("تقدّم البناء:")
        hdr.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {theme.HEADER};")
        layout.addWidget(hdr)

        self._status_lbl = QLabel("جارٍ التحضير...")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #1B5E20;")
        layout.addWidget(self._status_lbl)

        self._job_list = QListWidget()
        self._job_list.setLayoutDirection(Qt.RightToLeft)
        self._job_list.setMinimumHeight(200)
        self._job_list.setStyleSheet(
            "QListWidget {"
            "  border: 1px solid #C0CBDA; border-radius: 6px;"
            "  background: #F8FAFC; font-size: 12px;"
            "}"
            "QListWidget::item { padding: 8px 12px; border-bottom: 1px solid #E8EDF2; }"
        )
        layout.addWidget(self._job_list, stretch=1)

        self._results_lbl = QLabel("")
        self._results_lbl.setAlignment(Qt.AlignCenter)
        self._results_lbl.setStyleSheet("font-size: 12px; color: #455A64; margin-top: 4px;")
        layout.addWidget(self._results_lbl)

        btn_row = QHBoxLayout()
        self._close_btn = QPushButton("إغلاق")
        self._close_btn.setStyleSheet(_STYLE_SECONDARY)
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._on_close)
        btn_row.addStretch()
        btn_row.addWidget(self._close_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------

    def start(self, jobs: list[BatchJob]) -> None:
        """Initialise the list and kick off the thread."""
        self._total = len(jobs)
        self._job_list.clear()
        self._items.clear()

        for i, job in enumerate(jobs):
            label = self._item_label(i + 1, self._total, job, "pending", None)
            item = QListWidgetItem(label)
            self._job_list.addItem(item)
            self._items.append(item)

        runner = BatchRunner(self._codes)
        self._thread = BatchThread(runner, jobs, parent=self)
        self._thread.job_started.connect(self._on_job_started)
        self._thread.job_done.connect(self._on_job_done)
        self._thread.all_done.connect(self._on_all_done)
        self._thread.start()

    def _item_label(
        self,
        num: int,
        total: int,
        job: BatchJob,
        state: str,
        result: BatchJobResult | None,
    ) -> str:
        icon = _STATUS_ICONS.get(state, "")
        base = f"وظيفة {num}/{total}: {job.project_id} — {job.owner_id}  {icon}"
        if result and result.success:
            base += f"  ({result.elapsed_seconds:.1f} ث)"
        elif result and not result.success:
            err = (result.error_ar or "")[:60]
            base += f"  [{err}]"
        return base

    def _on_job_started(self, idx: int, total: int, job_id: str) -> None:
        self._status_lbl.setText(f"يُعالج الوظيفة {idx + 1} من {total}...")
        if idx < len(self._items):
            item = self._items[idx]
            # Reconstruct label with "running" state — job object not stored, just update text
            text = item.text()
            # Replace the pending icon with running icon
            text = text.replace(_STATUS_ICONS["pending"], _STATUS_ICONS["running"])
            item.setText(text)
            self._job_list.scrollToItem(item)

    def _on_job_done(self, result: object) -> None:
        r: BatchJobResult = result  # type: ignore[assignment]
        # Find the item whose text contains the job_id (encoded in the label as e.g. job_001)
        # We match by index order instead: results come in order
        done_count = sum(1 for i in self._items if "✅" in i.text() or "✗" in i.text())
        idx = done_count  # 0-based index of this result
        if idx < len(self._items):
            item = self._items[idx]
            state = "done_ok" if r.success else "done_err"
            # Build updated label
            text = item.text()
            # Replace running icon with done icon
            for old_icon in (_STATUS_ICONS["running"], _STATUS_ICONS["pending"]):
                text = text.replace(old_icon, "")
            icon = _STATUS_ICONS[state]
            suffix = f"  ({r.elapsed_seconds:.1f} ث)" if r.success else f"  [{(r.error_ar or '')[:50]}]"
            item.setText(text.rstrip() + f"  {icon}{suffix}")
            if r.success:
                item.setForeground(item.foreground())  # keep default
            else:
                from PyQt5.QtGui import QColor
                item.setForeground(QColor(theme.DEV_RED))

    def _on_all_done(self, results: list) -> None:
        results_typed: list[BatchJobResult] = results
        ok = sum(1 for r in results_typed if r.success)
        fail = len(results_typed) - ok
        self._status_lbl.setText(
            f"✅ اكتمل البناء: {ok} ناجح" + (f"  |  {fail} فشل" if fail else "")
        )
        self._status_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold;"
            + (f" color: {theme.DEV_RED};" if fail else " color: #1B5E20;")
        )
        self._results_lbl.setText(
            f"الوظائف الناجحة: {ok} / {len(results_typed)}"
        )
        self._close_btn.setEnabled(True)
        self.all_done.emit(results_typed)

    def _on_close(self) -> None:
        p = self.parent()
        while p and not isinstance(p, QDialog):
            p = p.parent()
        if p:
            p.accept()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()


# ─────────────────────────────────────────────────────────────────────────────
# Main dialog
# ─────────────────────────────────────────────────────────────────────────────

class BatchBuildDialog(QDialog):
    """Two-step dialog: job list → progress.

    Args:
        codes:        Full codes registry dict (registry["codes"]).
        presets_path: Path to presets.json.
        output_dir:   Directory where output .docx files will be saved.
        parent:       Parent widget.
    """

    def __init__(
        self,
        codes: dict,
        presets_path: Path,
        output_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("بناء متعدد المشاريع")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(600, 480)
        self.setModal(True)

        self._codes = codes
        self._presets_path = presets_path
        self._output_dir = output_dir

        # ── Stack ──────────────────────────────────────────────────────
        self._stack = QStackedWidget(self)

        self._job_list_screen = _JobListScreen(presets_path, output_dir, parent=self)
        self._progress_screen = _ProgressScreen(codes, parent=self)

        self._stack.addWidget(self._job_list_screen)   # index 0
        self._stack.addWidget(self._progress_screen)   # index 1

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self._stack)

        # ── Signals ────────────────────────────────────────────────────
        self._job_list_screen.build_requested.connect(self._start_batch)
        self._progress_screen.all_done.connect(self._on_all_done)

        # Show job list screen first
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------

    def _start_batch(self, jobs: list[BatchJob]) -> None:
        """Switch to progress screen and kick off the batch."""
        # Ensure output dir exists
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(
                self,
                "تعذّر تجهيز مجلد المخرجات",
                f"لم أتمكن من إنشاء مجلد الحفظ:\n{exc}",
            )
            return

        self._stack.setCurrentIndex(1)
        self._progress_screen.start(jobs)

    def _on_all_done(self, results: list[BatchJobResult]) -> None:
        ok = sum(1 for r in results if r.success)
        logger.info("Batch done: %d/%d succeeded", ok, len(results))

    # ------------------------------------------------------------------
    # Prevent closing while the batch is running
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._progress_screen.is_running():
            QMessageBox.information(
                self,
                "البناء جارٍ",
                "يرجى الانتظار حتى اكتمال جميع الوظائف.",
            )
            event.ignore()
        else:
            super().closeEvent(event)
