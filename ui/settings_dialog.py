#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Simple application settings dialog for ATPAS."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QSettings, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Expose common runtime settings without editing JSON files."""

    settings_changed = pyqtSignal()

    _KEY_AUTO_BACKUP = "autoBackupOnClose"
    _KEY_RESTORE_DRAFT = "restoreDraftPrompt"
    _KEY_OUTPUT_DIR = "output/customDir"
    _KEY_USE_OUTPUT_DIR = "output/useCustomDir"

    def __init__(self, settings: QSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("الإعدادات")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(560)
        self.setModal(True)

        self._settings = settings
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("إعدادات التشغيل")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #152433; "
            "padding-bottom: 6px; border-bottom: 2px solid #C9921B;"
        )
        root.addWidget(title)

        self._auto_backup = QCheckBox("إنشاء نسخة احتياطية تلقائياً عند إغلاق التطبيق")
        self._restore_draft = QCheckBox("سؤالي عن استعادة آخر جلسة عند فتح التطبيق")
        for cb in (self._auto_backup, self._restore_draft):
            cb.setLayoutDirection(Qt.RightToLeft)
            cb.setStyleSheet("font-weight: 600; color: #1C3045;")
            root.addWidget(cb)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        root.addWidget(sep)

        self._use_custom_output = QCheckBox("استخدام مجلد مخصص لحفظ عروض Word")
        self._use_custom_output.setLayoutDirection(Qt.RightToLeft)
        self._use_custom_output.setStyleSheet("font-weight: 700; color: #1C3045;")
        self._use_custom_output.stateChanged.connect(self._sync_output_controls)
        root.addWidget(self._use_custom_output)

        output_row = QWidget()
        output_l = QHBoxLayout(output_row)
        output_l.setContentsMargins(0, 0, 0, 0)
        output_l.setSpacing(8)

        self._output_edit = QLineEdit()
        self._output_edit.setLayoutDirection(Qt.LeftToRight)
        self._output_edit.setAlignment(Qt.AlignLeft)
        self._output_edit.setPlaceholderText("مثال: D:\\ATPAS_Output")

        browse_btn = QPushButton("اختيار...")
        browse_btn.clicked.connect(self._browse_output_dir)

        output_l.addWidget(self._output_edit, stretch=1)
        output_l.addWidget(browse_btn)
        self._browse_btn = browse_btn
        root.addWidget(output_row)

        hint = QLabel(
            "عند تعطيل المجلد المخصص سيحفظ التطبيق داخل output/generated_documents "
            "بجوار نسخة التشغيل."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #5A6B7C; font-size: 11px;")
        root.addWidget(hint)

        root.addStretch()

        actions = QHBoxLayout()
        reset_welcome = QPushButton("إظهار دليل البداية مرة أخرى")
        reset_welcome.clicked.connect(self._reset_welcome)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.setObjectName("settingsSaveBtn")
        save_btn.clicked.connect(self._save)

        actions.addWidget(reset_welcome)
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(save_btn)
        root.addLayout(actions)

        self.setStyleSheet(
            """
            QDialog {
                background: #FEFCF7;
                color: #121B28;
            }
            QPushButton#settingsSaveBtn {
                background: #2B7549;
                color: white;
                border: none;
                font-weight: 800;
            }
            QPushButton#settingsSaveBtn:hover {
                background: #236040;
            }
            """
        )

    def _load(self) -> None:
        self._auto_backup.setChecked(
            self._settings.value(self._KEY_AUTO_BACKUP, False, type=bool)
        )
        self._restore_draft.setChecked(
            self._settings.value(self._KEY_RESTORE_DRAFT, True, type=bool)
        )
        self._use_custom_output.setChecked(
            self._settings.value(self._KEY_USE_OUTPUT_DIR, False, type=bool)
        )
        self._output_edit.setText(
            str(self._settings.value(self._KEY_OUTPUT_DIR, "") or "")
        )
        self._sync_output_controls()

    def _sync_output_controls(self) -> None:
        enabled = self._use_custom_output.isChecked()
        self._output_edit.setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)

    def _browse_output_dir(self) -> None:
        start = self._output_edit.text().strip() or str(Path.home() / "Desktop")
        path = QFileDialog.getExistingDirectory(self, "اختر مجلد حفظ العروض", start)
        if path:
            self._output_edit.setText(path)

    def _save(self) -> None:
        output_dir = self._output_edit.text().strip()
        if self._use_custom_output.isChecked():
            if not output_dir:
                QMessageBox.warning(self, "إعداد غير مكتمل", "اختر مجلد حفظ العروض أولاً.")
                return
            try:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(
                    self,
                    "تعذّر استخدام المجلد",
                    f"لم أتمكن من إنشاء أو الوصول إلى مجلد الحفظ:\n{exc}",
                )
                return

        self._settings.setValue(self._KEY_AUTO_BACKUP, self._auto_backup.isChecked())
        self._settings.setValue(self._KEY_RESTORE_DRAFT, self._restore_draft.isChecked())
        self._settings.setValue(self._KEY_USE_OUTPUT_DIR, self._use_custom_output.isChecked())
        self._settings.setValue(self._KEY_OUTPUT_DIR, output_dir)
        self._settings.sync()
        self.settings_changed.emit()
        QMessageBox.information(self, "تم الحفظ", "تم حفظ الإعدادات بنجاح.")
        self.accept()

    def _reset_welcome(self) -> None:
        from ui.welcome_overlay import _get_marker_path

        marker = _get_marker_path()
        try:
            marker.unlink(missing_ok=True)
            QMessageBox.information(
                self,
                "تم",
                "سيظهر دليل البداية عند فتح التطبيق مرة أخرى.",
            )
        except OSError as exc:
            QMessageBox.warning(self, "تعذّر التحديث", f"تعذّر إعادة ضبط دليل البداية:\n{exc}")


def resolve_output_dir(settings: QSettings) -> Path:
    """Return the configured output directory, falling back to the app default."""
    use_custom = settings.value(SettingsDialog._KEY_USE_OUTPUT_DIR, False, type=bool)
    custom_dir = str(settings.value(SettingsDialog._KEY_OUTPUT_DIR, "") or "").strip()
    if use_custom and custom_dir:
        return Path(custom_dir)
    if getattr(__import__("sys"), "frozen", False):
        import sys as _sys

        return Path(_sys.executable).parent / "output" / "generated_documents"
    return Path("output/generated_documents")
