#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-005: Build worker (QThread) + progress dialog.

BuildWorker   — runs Builder.build() off the UI thread.
               Emits step_changed(int, str) for progress steps.
               Emits finished(bool, str, str) → (success, error_ar, output_path).

BuildProgressDialog — modal dialog: progress bar, step log, open-file/folder buttons.

Design notes:
  - Window flags are NOT changed after creation (avoid HWND recreation on Windows
    which can break the exec_() event loop).
  - closeEvent blocks closing while the worker thread is running.
  - On success, shows the full absolute path + "Open File" + "Open Folder" buttons.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)

from engine.builder import Builder
from ui.motion import motion_ms, motion_single_shot, prefers_reduced_motion
from ui.build_report import BuildReportDialog
from ui.build_history import BuildHistoryManager


class BuildWorker(QThread):
    """Off-thread builder — keeps the UI responsive during document generation."""

    step_changed = pyqtSignal(int, str)   # (percent, arabic_message)
    finished = pyqtSignal(bool, str, str) # (success, error_ar, output_path)

    def __init__(
        self,
        codes: dict[str, Any],
        selected_codes: list[str],
        project_id: str,
        owner_id: str,
        output_path: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._codes = codes
        self._selected_codes = selected_codes
        self._project_id = project_id
        self._owner_id = owner_id
        self._output_path = output_path

    def run(self) -> None:
        try:
            self.step_changed.emit(10, "فحص أكواد المشروع والتحقق من صحتها...")
            builder = Builder(self._codes)

            self.step_changed.emit(30, "ترتيب البنود وحل التبعيات الهندسية...")
            self.step_changed.emit(50, "تجميع فقرات العرض الفني ونصوص الأنشطة...")

            success, error_ar = builder.build(
                selected_codes=self._selected_codes,
                project_id=self._project_id,
                owner_id=self._owner_id,
                output_path=self._output_path,
                skip_validation=True,   # already validated in UI before dialog opens
            )

            if success:
                self.step_changed.emit(90, "تطبيق تنسيق الرواف وضبط الجداول...")
                self.step_changed.emit(100, "العرض الفني جاهز للتقديم ✓")
                self.finished.emit(True, "", str(self._output_path))
            else:
                self.finished.emit(False, error_ar or "خطأ غير معروف", "")

        except Exception as exc:  # noqa: BLE001
            self.finished.emit(False, f"خطأ غير متوقع: {exc}", "")


class BuildProgressDialog(QDialog):
    """Modal progress dialog shown while BuildWorker is running."""

    #: يُطلق عند طلب المستخدم بناء عرض جديد من تقرير البناء
    new_build_requested = pyqtSignal()

    def __init__(
        self,
        codes: dict[str, Any],
        selected_codes: list[str],
        project_id: str,
        owner_id: str,
        output_dir: Path,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("جارٍ بناء العرض الفني...")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(520)
        self.setModal(True)
        # NOTE: Do NOT remove Qt.WindowCloseButtonHint via setWindowFlags().
        # On Windows, changing native window flags destroys/recreates the HWND,
        # which can break exec_().  We block closing via closeEvent() instead.

        self._build_running = False
        self._build_start_time: float = 0.0   # set in start_build()
        self._elapsed_seconds: float = 0.0    # computed in _on_finished()

        # Keep a reference to codes for BuildReportDialog + history
        self._codes = codes
        self._selected_codes = selected_codes
        self._project_id = project_id
        self._owner_id   = owner_id
        self._history_mgr = BuildHistoryManager()

        # Smooth progress-bar animation — reused for every step
        # (initialised after the progress bar widget is created below)
        self._bar_anim: QPropertyAnimation | None = None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_path = output_dir / f"proposal_{project_id}_{owner_id}_{timestamp}.docx"

        # ── Widgets ────────────────────────────────────────────────────
        self._status_label = QLabel("جارٍ التحضير...")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 4px;")
        self._status_opacity = QGraphicsOpacityEffect(self._status_label)
        self._status_opacity.setOpacity(1.0)
        self._status_label.setGraphicsEffect(self._status_opacity)
        self._status_anim = QPropertyAnimation(self._status_opacity, b"opacity", self)
        self._status_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)

        self._log = QListWidget()
        self._log.setMaximumHeight(150)
        self._log.setLayoutDirection(Qt.RightToLeft)

        # Output path display (shown on success)
        self._path_label = QLabel()
        self._path_label.setLayoutDirection(Qt.LeftToRight)
        self._path_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._path_label.setStyleSheet(
            "font-size: 10px; color: #2D7A4F; background: #EBF7F1; "
            "border-radius: 5px; padding: 4px 8px;"
        )
        self._path_label.setWordWrap(True)
        self._path_label.setVisible(False)

        # ── Buttons ────────────────────────────────────────────────────
        self._open_btn = QPushButton("📄 فتح الملف")
        self._open_btn.setVisible(False)
        self._open_btn.clicked.connect(self._open_output)

        self._folder_btn = QPushButton("📁 فتح المجلد")
        self._folder_btn.setVisible(False)
        self._folder_btn.clicked.connect(self._open_folder)

        self._report_btn = QPushButton("📊 تقرير البناء")
        self._report_btn.setVisible(False)
        self._report_btn.setStyleSheet(
            "QPushButton {"
            "  background: #152433; color: #C9921B;"
            "  border: none; border-radius: 6px;"
            "  padding: 6px 16px; font-size: 12px; font-weight: 700;"
            "}"
            "QPushButton:hover { background: #1C3045; }"
        )
        self._report_btn.clicked.connect(self._open_report_dialog)

        self._close_btn = QPushButton("إغلاق")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self.accept)

        action_row = QHBoxLayout()
        action_row.addWidget(self._open_btn)
        action_row.addWidget(self._folder_btn)
        action_row.addStretch()
        action_row.addWidget(self._report_btn)
        action_row.addWidget(self._close_btn)

        # ── Layout ─────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._log)
        layout.addWidget(self._path_label)
        layout.addLayout(action_row)

        # ── Progress bar animation (single instance, reused per step) ──
        self._bar_anim = QPropertyAnimation(self._progress_bar, b"value", self)
        self._bar_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ── Worker ─────────────────────────────────────────────────────
        self._worker = BuildWorker(
            codes=codes,
            selected_codes=selected_codes,
            project_id=project_id,
            owner_id=owner_id,
            output_path=self._output_path,
            parent=self,
        )
        self._worker.step_changed.connect(self._on_step)
        self._worker.finished.connect(self._on_finished)

    def start_build(self) -> None:
        self._build_running = True
        self._build_start_time = time.monotonic()
        self._worker.start()

    # ------------------------------------------------------------------
    # Event overrides
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Block the native close (X button) while the build is running."""
        if self._build_running:
            event.ignore()
        else:
            super().closeEvent(event)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_step(self, percent: int, message: str) -> None:
        self._status_label.setText(message)
        if prefers_reduced_motion():
            self._progress_bar.setValue(percent)
            self._status_opacity.setOpacity(1.0)
        else:
            # Animate progress bar smoothly to the new value.
            # Stop any running animation first to avoid competing targets.
            if self._bar_anim.state() != QPropertyAnimation.Stopped:
                self._bar_anim.stop()
            self._bar_anim.setDuration(motion_ms(180))
            self._bar_anim.setStartValue(self._progress_bar.value())
            self._bar_anim.setEndValue(percent)
            self._bar_anim.start()

            # Subtle status fade-in confirms each step transition.
            if self._status_anim.state() != QPropertyAnimation.Stopped:
                self._status_anim.stop()
            self._status_anim.setDuration(motion_ms(220))
            self._status_anim.setStartValue(0.55)
            self._status_anim.setEndValue(1.0)
            self._status_opacity.setOpacity(0.55)
            self._status_anim.start()

        item = QListWidgetItem(f"{percent:3d}%  {message}")
        self._log.addItem(item)
        self._log.scrollToBottom()

    def _on_finished(self, success: bool, error_ar: str, output_path: str) -> None:
        self._build_running = False
        self._close_btn.setEnabled(True)
        # NOTE: No setWindowFlags() here — it would recreate the HWND and break exec_()

        if success:
            self._elapsed_seconds = time.monotonic() - self._build_start_time

            # ── حفظ في سجل البنات ───────────────────────────────────────
            page_count = sum(
                int(c.get("page_count", 0))
                for c in self._codes.values()
                if c.get("code_id") in self._selected_codes
                or (isinstance(c, dict) and c.get("code_id") in self._selected_codes)
            )
            # simpler: count pages from selected codes directly
            page_count = sum(
                int(self._codes.get(cid, {}).get("page_count", 0))
                for cid in self._selected_codes
            )
            self._history_mgr.save_entry(
                project_id=self._project_id,
                owner_id=self._owner_id,
                codes=self._selected_codes,
                output_file=str(self._output_path),
                elapsed_seconds=self._elapsed_seconds,
                page_count=page_count,
            )

            self._progress_bar.setValue(100)
            self._status_label.setText("✅ العرض الفني جاهز للتقديم")
            self._status_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; padding: 4px; color: #1B5E20;"
            )
            # Golden shimmer: briefly brighten the progress bar, then restore
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background: #E0B040; border-radius: 8px; }"
            )
            motion_single_shot(
                700,
                lambda: self._progress_bar.setStyleSheet(
                    "QProgressBar::chunk { "
                    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 #A87220, stop:1 #C8912A); "
                    "border-radius: 8px; }"
                ),
            )

            # Show absolute path with fade-in animation
            abs_path = str(Path(output_path).resolve())
            self._path_label.setText(f"📂 {abs_path}")
            self._fade_in(self._path_label)
            self._log.addItem(QListWidgetItem(f"✓ الملف: {abs_path}"))

            # Reveal action buttons with staggered fade-in
            # Report button appears last (highlighted, draws attention)
            self._fade_in(self._open_btn,    delay_ms=120)
            self._fade_in(self._folder_btn,  delay_ms=220)
            self._fade_in(self._report_btn,  delay_ms=340)
        else:
            self._progress_bar.setStyleSheet(
                "QProgressBar::chunk { background: #C62828; }"
            )
            self._status_label.setText("✗ تعذّر إنشاء العرض الفني")
            self._status_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; padding: 4px; color: #C62828;"
            )
            self._log.addItem(QListWidgetItem(f"الخطأ: {error_ar}"))

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------

    def _fade_in(self, widget, duration_ms: int = 350, delay_ms: int = 0) -> None:
        """Make a widget visible with an opacity fade-in animation.

        Uses QGraphicsOpacityEffect + QPropertyAnimation so no layout
        properties are animated (safe on all platforms).
        """
        if prefers_reduced_motion():
            widget.setGraphicsEffect(None)
            widget.setVisible(True)
            return

        def _start() -> None:
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)
            widget.setVisible(True)

            anim = QPropertyAnimation(effect, b"opacity", widget)
            anim.setDuration(motion_ms(duration_ms))
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.finished.connect(lambda: widget.setGraphicsEffect(None))
            anim.start(QPropertyAnimation.DeleteWhenStopped)

        if delay_ms:
            motion_single_shot(delay_ms, _start)
        else:
            _start()

    # ------------------------------------------------------------------
    # Build report
    # ------------------------------------------------------------------

    def _open_report_dialog(self) -> None:
        """Close this dialog and open the detailed post-build report."""
        report = BuildReportDialog(
            output_path=self._output_path,
            selected_codes=self._selected_codes,
            registry_codes=self._codes,
            elapsed_seconds=self._elapsed_seconds,
            parent=self.parent(),
        )
        report.new_build_requested.connect(self.new_build_requested.emit)
        self.accept()       # close progress dialog first
        report.exec_()      # then open report (uses parent = MainWindow)

    # ------------------------------------------------------------------
    # File / folder openers
    # ------------------------------------------------------------------

    def _open_output(self) -> None:
        """Open the generated document in Word (or default .docx handler)."""
        path = self._output_path.resolve()
        if not path.exists():
            QMessageBox.warning(self, "تحذير", f"الملف غير موجود:\n{path}")
            return

        try:
            if sys.platform == "win32":
                os.startfile(str(path))
                return

            cmd = ["open", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path)]
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                raise RuntimeError(f"Open command failed with exit code {result.returncode}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "تعذّر فتح الملف", f"تعذّر فتح الملف:\n{exc}")

    def _open_folder(self) -> None:
        """Open Windows Explorer with the output file selected."""
        path = self._output_path.resolve()
        folder = path.parent
        if not folder.exists():
            QMessageBox.warning(self, "تحذير", f"مجلد المخرجات غير موجود:\n{folder}")
            return

        try:
            if sys.platform == "win32":
                if path.exists():
                    # /select, highlights the file in the folder
                    result = subprocess.run(["explorer", f"/select,{path}"], check=False)
                else:
                    result = subprocess.run(["explorer", str(folder)], check=False)
            elif sys.platform == "darwin":
                cmd = ["open", "-R", str(path)] if path.exists() else ["open", str(folder)]
                result = subprocess.run(cmd, check=False)
            else:
                result = subprocess.run(["xdg-open", str(folder)], check=False)

            if result.returncode != 0:
                raise RuntimeError(f"Open command failed with exit code {result.returncode}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "تعذّر فتح المجلد", f"تعذّر فتح المجلد:\n{exc}")
