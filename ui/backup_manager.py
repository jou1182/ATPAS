#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-013: Data Backup and Restore Manager.

- Creates timestamped ZIP archives of all critical JSON data files.
- Lists existing backups with size / date metadata.
- Restores any backup with a single click (with confirmation).
- Deletes unwanted backups.
- Exposes create_backup() for programmatic use (e.g. auto-backup on close).
"""

from __future__ import annotations

import logging
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ── Files and directories included in every backup ────────────────────────────
_BACKUP_DIR  = Path("backups")

_DATA_FILES: list[str] = [
    "codes_registry.json",
    "master_config.json",
    "presets.json",
    "build_history.json",
]

_DATA_DIRS: list[str] = [
    "metadata/owner_specifications",
    "templates/style_templates",
]


# ── Standalone helper ─────────────────────────────────────────────────────────

def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    """Extract a ZIP safely — reject path traversal (Zip-Slip) members.

    Every member's resolved target must stay inside ``dest``; otherwise
    a ValueError is raised before anything is written.
    """
    dest_resolved = dest.resolve()
    for info in zf.infolist():
        target = (dest / info.filename).resolve()
        if not str(target).startswith(str(dest_resolved) + os.sep) and target != dest_resolved:
            raise ValueError(
                f"مدخل غير آمن في النسخة الاحتياطية: {info.filename}"
            )
        if info.filename.endswith("/"):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            out.write(src.read())


def create_backup(label: str = "") -> Path:
    """Create a timestamped ZIP backup and return its path.

    Args:
        label: Optional suffix appended to the filename (e.g. ``"auto"``).

    Returns:
        Path to the newly created ZIP file.

    Raises:
        OSError / zipfile.BadZipFile on failure.
    """
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts     = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    zip_path = _BACKUP_DIR / f"ATPAS_backup_{ts}{suffix}.zip"

    logger.info("Creating backup: %s (label=%r)", zip_path.name, label)
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for fname in _DATA_FILES:
            p = Path(fname)
            if p.exists():
                zf.write(p, fname)
                file_count += 1

        for dname in _DATA_DIRS:
            d = Path(dname)
            if d.exists():
                for f in sorted(d.rglob("*")):
                    if f.is_file():
                        zf.write(f, str(f.relative_to(Path("."))))
                        file_count += 1

    size_kb = zip_path.stat().st_size / 1024
    logger.info("Backup complete: %s (%d files, %.1f KB)", zip_path.name, file_count, size_kb)
    return zip_path


def list_backups() -> list[Path]:
    """Return existing backup ZIPs sorted newest-first."""
    if not _BACKUP_DIR.exists():
        return []
    return sorted(_BACKUP_DIR.glob("ATPAS_backup_*.zip"), reverse=True)


# ── Shared style helpers ──────────────────────────────────────────────────────

def _btn(text: str, color: str = "#2E7D91", danger: bool = False) -> QPushButton:
    bg   = "#C62828" if danger else color
    hov  = "#B71C1C" if danger else "#1B5E7D"
    btn  = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {bg}; color: #FFFFFF;
            border: none; border-radius: 6px;
            font-size: 12px; font-weight: 700;
            padding: 8px 20px;
        }}
        QPushButton:hover {{ background: {hov}; }}
        QPushButton:pressed {{ background: {hov}CC; }}
        QPushButton:disabled {{
            background: #B0BEC5; color: #78909C;
        }}
    """)
    return btn


# ── Dialog ────────────────────────────────────────────────────────────────────

class BackupDialog(QDialog):
    """Browse, create, restore and delete ATPAS data backups."""

    #: Emitted after a successful restore so MainWindow can reload data.
    restore_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("النسخ الاحتياطي والاستعادة")
        self.setMinimumSize(540, 460)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("QDialog { background: #F2EFE9; }")
        self._setup_ui()
        self._load_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header ─────────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(60)
        hdr.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #152433, stop:1 #1C3045);
                border-bottom: 3px solid #C9921B;
            }
        """)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(18, 0, 18, 0)
        icon_lbl = QLabel("🗄️")
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        title_lbl = QLabel("إدارة النسخ الاحتياطية")
        title_lbl.setStyleSheet(
            "color: #C9921B; font-size: 16px; font-weight: 800; background: transparent;"
        )
        sub_lbl = QLabel("codes_registry · master_config · presets · owner_specifications")
        sub_lbl.setStyleSheet(
            "color: #7BA0BC; font-size: 10px; background: transparent;"
        )
        hdr_l.addWidget(icon_lbl)
        hdr_l.addSpacing(8)
        hdr_l.addWidget(title_lbl)
        hdr_l.addSpacing(16)
        hdr_l.addWidget(sub_lbl)
        hdr_l.addStretch()
        root.addWidget(hdr)

        # ── body ───────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("QWidget { background: #F2EFE9; }")
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(18, 14, 18, 14)
        body_l.setSpacing(10)
        root.addWidget(body, stretch=1)

        # info label
        self._info_lbl = QLabel("اختر نسخة من القائمة أدناه:")
        self._info_lbl.setStyleSheet(
            "color: #30465E; font-size: 12px; font-weight: 600;"
        )
        body_l.addWidget(self._info_lbl)

        # backup list
        self._list = QListWidget()
        self._list.setLayoutDirection(Qt.RightToLeft)
        self._list.setStyleSheet("""
            QListWidget {
                background: #FFFFFF;
                border: 1px solid #C8D8E8;
                border-radius: 8px;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-bottom: 1px solid #EAF0F8;
                color: #1C3045;
            }
            QListWidget::item:selected {
                background: #D4EAFA;
                color: #0D2A3D;
                border-left: 3px solid #1E7BC4;
            }
            QListWidget::item:hover:!selected {
                background: #EBF4FC;
            }
        """)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        body_l.addWidget(self._list, stretch=1)

        # detail label
        self._detail_lbl = QLabel("")
        self._detail_lbl.setStyleSheet(
            "color: #5B6672; font-size: 11px; padding: 2px 4px;"
        )
        self._detail_lbl.setAlignment(Qt.AlignRight)
        body_l.addWidget(self._detail_lbl)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #DEDAD4;")
        body_l.addWidget(sep)

        # action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._create_btn = _btn("💾  إنشاء نسخة احتياطية", "#1B5E7D")
        self._create_btn.setToolTip("إنشاء نسخة احتياطية الآن من جميع البيانات")
        self._create_btn.clicked.connect(self._on_create)

        self._restore_btn = _btn("↩  استعادة المختارة", "#2E7D32")
        self._restore_btn.setToolTip("استعادة البيانات من النسخة المحددة")
        self._restore_btn.setEnabled(False)
        self._restore_btn.clicked.connect(self._on_restore)

        self._delete_btn = _btn("🗑  حذف", danger=True)
        self._delete_btn.setToolTip("حذف النسخة الاحتياطية المحددة نهائياً")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete)

        close_btn = QPushButton("إغلاق")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #5B6672;
                border: 1px solid #C0C8D0; border-radius: 6px;
                font-size: 12px; padding: 8px 18px;
            }
            QPushButton:hover { background: #E8E4DC; }
        """)
        close_btn.clicked.connect(self.reject)

        btn_row.addWidget(self._create_btn)
        btn_row.addWidget(self._restore_btn)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        body_l.addLayout(btn_row)

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    def _load_list(self) -> None:
        self._list.clear()
        backups = list_backups()

        if not backups:
            placeholder = QListWidgetItem("ℹ  لا توجد نسخ احتياطية — اضغط «إنشاء نسخة» للبدء")
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setForeground(Qt.gray)
            self._list.addItem(placeholder)
            self._info_lbl.setText("لا توجد نسخ احتياطية بعد:")
            return

        self._info_lbl.setText(f"النسخ الاحتياطية المتاحة ({len(backups)}):")
        for i, path in enumerate(backups):
            size_kb    = path.stat().st_size // 1024
            mtime      = datetime.fromtimestamp(path.stat().st_mtime)
            date_str   = mtime.strftime("%Y-%m-%d  %H:%M")
            label_tag  = "  🔴 تلقائية" if "_auto" in path.name else ""
            text = f"📦  {path.stem.replace('ATPAS_backup_', '')}  •  {size_kb} KB  •  {date_str}{label_tag}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, str(path))
            if i == 0:
                item.setToolTip("أحدث نسخة احتياطية")
            self._list.addItem(item)

    def _on_selection_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        valid = current is not None and bool(current.data(Qt.UserRole))
        self._restore_btn.setEnabled(valid)
        self._delete_btn.setEnabled(valid)
        if valid:
            path = Path(current.data(Qt.UserRole))
            size_mb = path.stat().st_size / 1_048_576
            self._detail_lbl.setText(
                f"المسار: {path}  •  الحجم: {size_mb:.2f} MB"
            )
        else:
            self._detail_lbl.setText("")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_create(self) -> None:
        self._create_btn.setEnabled(False)
        self._create_btn.setText("⏳  جاري الحفظ...")
        try:
            path = create_backup()
            self._load_list()
            self._create_btn.setText("✅  تم!")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._create_btn.setText("💾  إنشاء نسخة احتياطية"))
            QTimer.singleShot(1500, lambda: self._create_btn.setEnabled(True))
            self._detail_lbl.setText(f"تم الحفظ: {path.name}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("Backup creation failed")
            self._create_btn.setText("💾  إنشاء نسخة احتياطية")
            self._create_btn.setEnabled(True)
            QMessageBox.critical(self, "خطأ", f"تعذّر إنشاء النسخة الاحتياطية:\n{exc}")

    def _on_restore(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        path = Path(item.data(Qt.UserRole))

        reply = QMessageBox.question(
            self,
            "تأكيد الاستعادة",
            f"سيتم استبدال البيانات الحالية بنسخة:\n\n"
            f"    {path.name}\n\n"
            f"هذا الإجراء لا يمكن التراجع عنه.\n"
            f"هل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        logger.info("Restoring backup: %s", path.name)
        try:
            with zipfile.ZipFile(path, "r") as zf:
                _safe_extract(zf, Path("."))
            logger.info("Backup restored successfully: %s", path.name)
            QMessageBox.information(
                self,
                "تمت الاستعادة",
                "تم استعادة البيانات بنجاح.\n\nسيتم تحديث الواجهة تلقائياً.",
            )
            self.restore_requested.emit()
            self.accept()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Backup restore failed: %s", path.name)
            QMessageBox.critical(
                self, "خطأ", f"تعذّر استعادة النسخة الاحتياطية:\n{exc}"
            )

    def _on_delete(self) -> None:
        item = self._list.currentItem()
        if not item:
            return
        path = Path(item.data(Qt.UserRole))

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"حذف النسخة الاحتياطية:\n\n    {path.name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            path.unlink()
            logger.info("Backup deleted: %s", path.name)
            self._load_list()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to delete backup: %s", path.name)
            QMessageBox.critical(self, "خطأ", f"تعذّر الحذف:\n{exc}")
