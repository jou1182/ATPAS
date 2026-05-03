#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""نافذة عرض واسترجاع الجلسات المحفوظة (Smart Session Memory).

تظهر قائمة بآخر 10 جلسات عمل مع إمكانية:
- استرجاع جلسة (تطبيق المشروع والجهة والأكواد)
- حذف جلسة
- مسح الكل
- رؤية تفاصيل كل جلسة (عدد الأكواد، الصفحات، التاريخ)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.theme import (
    ACCENT, ACCENT_PALE, BORDER, BORDER2, ERROR, ERROR_PALE,
    SUCCESS, SURFACE, TEXT, TEXT2, WARNING, WARNING_PALE,
)
from utils.session_memory import (
    clear_all_sessions,
    count_sessions,
    delete_session,
    get_sessions,
    restore_session,
)


class SessionHistoryDialog(QDialog):
    """نافذة عرض الجلسات المحفوظة مع إمكانية الاسترجاع والحذف."""

    # يُطلق عند طلب استرجاع جلسة — MainWindow يستمع ويطبق الاختيار
    session_restored = pyqtSignal(list, str, list)  # project_ids, owner_id, codes

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("📋  الجلسات المحفوظة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(620)
        self.setMinimumHeight(420)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._sessions = get_sessions()
        self._build_ui()
        self._populate_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # ── عنوان ──────────────────────────────────────────────────────
        title_row = QHBoxLayout()

        title_lbl = QLabel("📋  الجلسات المحفوظة")
        title_lbl.setStyleSheet(
            "font-size: 16px; font-weight: 800; color: #152433;"
        )

        count_lbl = QLabel(f"({len(self._sessions)} جلسة)")
        count_lbl.setStyleSheet(
            "font-size: 12px; color: #5A6B7C; padding-top: 4px;"
        )

        title_row.addWidget(title_lbl)
        title_row.addWidget(count_lbl)
        title_row.addStretch()
        layout.addLayout(title_row)

        # ── فاصل ───────────────────────────────────────────────────────
        sep = QWidget()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background: #C9921B; border-radius: 1px;")
        layout.addWidget(sep)

        # ── قائمة الجلسات ──────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setLayoutDirection(Qt.RightToLeft)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: #FDFCF8;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-radius: 6px;
                color: {TEXT};
                border: 1px solid transparent;
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background: {ACCENT_PALE};
                color: {TEXT};
                border-left: 4px solid {ACCENT};
                font-weight: 500;
            }}
            QListWidget::item:hover:!selected {{
                background: #F5F0E8;
            }}
        """)
        self._list.itemDoubleClicked.connect(lambda _item: self._on_restore())
        self._list.currentRowChanged.connect(lambda _row: self._update_buttons())
        layout.addWidget(self._list, stretch=1)

        # ── أزرار التحكم ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        restore_btn = QPushButton("🔄  استرجاع الجلسة")
        restore_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SUCCESS}; color: white;
                border: none; border-radius: 6px;
                padding: 8px 20px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #236040; }}
            QPushButton:disabled {{ background: #AFBFB8; color: #E2EDE9; }}
        """)
        restore_btn.clicked.connect(self._on_restore)
        self._restore_btn = restore_btn

        delete_btn = QPushButton("🗑️  حذف")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ERROR_PALE}; color: {ERROR};
                border: 1px solid {ERROR}; border-radius: 6px;
                padding: 8px 20px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #FDDDDD; }}
            QPushButton:disabled {{ color: #CCC; border-color: #DDD; background: #F5F5F5; }}
        """)
        delete_btn.clicked.connect(self._on_delete)
        self._delete_btn = delete_btn

        clear_btn = QPushButton("🧹  مسح الكل")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {WARNING};
                border: 1px solid {WARNING}70; border-radius: 6px;
                padding: 8px 20px; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {WARNING_PALE}; }}
        """)
        clear_btn.clicked.connect(self._on_clear_all)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE};
                border: 1px solid {BORDER2}; border-radius: 6px;
                padding: 8px 20px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {ACCENT_PALE}; }}
        """)
        close_btn.clicked.connect(self.reject)

        btn_row.addWidget(restore_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        # تحديث حالة الأزرار
        self._update_buttons()

    def _populate_list(self) -> None:
        """ملء القائمة بالجلسات المحفوظة."""
        self._list.clear()

        if not self._sessions:
            empty_item = QListWidgetItem("📭  لا توجد جلسات محفوظة بعد")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsSelectable)
            empty_item.setForeground(QColor(TEXT2))
            self._list.addItem(empty_item)
            return

        for i, session in enumerate(self._sessions):
            label = session.get("label", "جلسة غير مسماة")
            code_count = session.get("code_count", 0)
            page_count = session.get("page_count", 0)
            pids = session.get("project_ids", [])
            oid = session.get("owner_id", "")
            ts = session.get("timestamp", 0)

            # تنسيق التاريخ للعرض
            date_str = ""
            if ts:
                dt = datetime.fromtimestamp(ts)
                date_str = dt.strftime("%d/%m/%Y %I:%M %p")

            projects_str = " + ".join(pids) if pids else "?"

            # نص العنصر مع تفاصيل
            display_text = (
                f"🕐  {date_str}\n"
                f"📁  {projects_str}  |  🏢  {oid}\n"
                f"📦  {code_count} كود  |  📄  {page_count} صفحة"
            )

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, i)  # تخزين index الجلسة
            hint = item.sizeHint()
            item.setSizeHint(QSize(hint.width(), hint.height() + 16))
            self._list.addItem(item)

    def _update_buttons(self) -> None:
        """تفعيل/تعطيل الأزرار حسب وجود جلسات واختيار."""
        has_sessions = len(self._sessions) > 0
        has_selection = self._list.currentRow() >= 0

        self._restore_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)
        # زر مسح الكل مفعل فقط إذا في جلسات
        # (نجده من الأزرار المضافة)

    def _get_selected_index(self) -> int | None:
        """إرجاع index الجلسة المختارة أو None."""
        item = self._list.currentItem()
        if item is None:
            return None
        idx = item.data(Qt.UserRole)
        if idx is None:
            return None
        return int(idx)

    def _on_restore(self) -> None:
        """استرجاع الجلسة المختارة."""
        idx = self._get_selected_index()
        if idx is None:
            return

        session = restore_session(idx)
        if session is None:
            QMessageBox.warning(
                self, "خطأ", "لم يتم العثور على الجلسة المطلوبة."
            )
            return

        pids = session.get("project_ids", [])
        oid = session.get("owner_id", "")
        codes = session.get("selected_codes", [])

        if not pids or not oid or not codes:
            QMessageBox.warning(
                self, "جلسة غير صالحة",
                "هذه الجلسة لا تحتوي على بيانات كافية للاسترجاع."
            )
            return

        # إرسال الإشارة للاسترجاع
        self.session_restored.emit(pids, oid, codes)
        self.accept()

    def _on_delete(self) -> None:
        """حذف الجلسة المختارة."""
        idx = self._get_selected_index()
        if idx is None:
            return

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذه الجلسة؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if delete_session(idx):
            # إعادة تحميل القائمة
            self._sessions = get_sessions()
            self._populate_list()
            self._update_buttons()

    def _on_clear_all(self) -> None:
        """مسح جميع الجلسات."""
        if not self._sessions:
            return

        reply = QMessageBox.question(
            self,
            "تأكيد مسح الكل",
            f"هل تريد مسح جميع الجلسات ({len(self._sessions)} جلسة)؟\n"
            "لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        clear_all_sessions()
        self._sessions = []
        self._populate_list()
        self._update_buttons()
