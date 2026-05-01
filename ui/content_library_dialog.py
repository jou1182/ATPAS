#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Content library management center for ATPAS source Word files."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from utils.activity_log import ActivityLog
from utils.content_approval import (
    STATUS_APPROVED,
    STATUS_NEEDS_REVIEW,
    STATUS_NO_FILE,
    STATUS_PRESENT,
    ContentApprovalManager,
)
from utils.content_library import ContentLibrary
from utils.word_content_audit import WordContentAudit, audit_code_content


_STATE_COLORS = {
    STATUS_APPROVED: ("#2B7549", "#EAF5EF"),
    STATUS_NEEDS_REVIEW: ("#B56618", "#FFF4E7"),
    STATUS_PRESENT: ("#1C5D85", "#EEF3FA"),
    STATUS_NO_FILE: ("#5A6B7C", "#F5F1E8"),
}


class ContentLibraryDialog(QDialog):
    """Review and approve the 64-code Word content library."""

    def __init__(self, registry_data: dict[str, Any], parent=None) -> None:
        super().__init__(parent)
        self._codes = registry_data.get("codes", {})
        self._library = ContentLibrary()
        self._approval = ContentApprovalManager()
        self._audits: dict[str, WordContentAudit] = {}
        self._states: dict[str, Any] = {}
        self._current_code: str = ""

        self.setWindowTitle("مركز إدارة مكتبة Word")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(920, 640)
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        title = QLabel("مركز إدارة مكتبة Word")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #152433; "
            "padding-bottom: 7px; border-bottom: 2px solid #C9921B;"
        )
        root.addWidget(title)

        self._summary = QLabel("")
        self._summary.setAlignment(Qt.AlignCenter)
        self._summary.setWordWrap(True)
        self._summary.setStyleSheet(
            "font-weight: 800; padding: 8px 12px; color: #152433; "
            "background: #FAF0DC; border: 1px solid #D5CFBF; border-radius: 8px;"
        )
        root.addWidget(self._summary)

        body = QHBoxLayout()
        body.setSpacing(10)

        self._list = QListWidget(self)
        self._list.setLayoutDirection(Qt.RightToLeft)
        self._list.currentItemChanged.connect(self._on_selected)
        body.addWidget(self._list, stretch=2)

        right = QVBoxLayout()
        self._details = QTextBrowser(self)
        self._details.setLayoutDirection(Qt.RightToLeft)
        right.addWidget(self._details, stretch=1)

        actions = QHBoxLayout()
        self._open_btn = QPushButton("فتح ملف Word")
        self._open_btn.clicked.connect(self._open_current)
        self._approve_btn = QPushButton("اعتماد المحتوى")
        self._approve_btn.clicked.connect(self._approve_current)
        self._review_btn = QPushButton("إرجاع للمراجعة")
        self._review_btn.clicked.connect(self._mark_review_current)
        refresh_btn = QPushButton("تحديث الفحص")
        refresh_btn.clicked.connect(self._reload)
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        actions.addWidget(self._open_btn)
        actions.addWidget(self._approve_btn)
        actions.addWidget(self._review_btn)
        actions.addStretch()
        actions.addWidget(refresh_btn)
        actions.addWidget(close_btn)
        right.addLayout(actions)

        body.addLayout(right, stretch=3)
        root.addLayout(body, stretch=1)

        self.setStyleSheet(
            """
            QDialog {
                background: #FEFCF7;
                color: #121B28;
            }
            QTextBrowser, QListWidget {
                background: #FFFFFF;
                border: 1px solid #D5CFBF;
                border-radius: 9px;
                padding: 6px;
            }
            QPushButton {
                min-width: 105px;
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid #C3BBAA;
                background: #FEFCF7;
                color: #121B28;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #FAF0DC;
                border-color: #C9921B;
                color: #A77218;
            }
            QPushButton:disabled {
                background: #EDEAE4;
                color: #9B9B9B;
            }
            """
        )

    def _reload(self) -> None:
        self._audits.clear()
        self._states.clear()
        self._list.clear()
        active_codes = [
            (code_id, data)
            for code_id, data in sorted(
                self._codes.items(),
                key=lambda item: int(item[1].get("sequence_order", 9999)),
            )
            if data.get("status") == "active"
        ]

        counts = {STATUS_APPROVED: 0, STATUS_NEEDS_REVIEW: 0, STATUS_PRESENT: 0, STATUS_NO_FILE: 0}
        for code_id, data in active_codes:
            audit = audit_code_content(code_id, data, self._library)
            state = self._approval.state_for(code_id, audit)
            self._audits[code_id] = audit
            self._states[code_id] = state
            counts[state.status] = counts.get(state.status, 0) + 1

            color, bg = _STATE_COLORS.get(state.status, ("#5A6B7C", "#F5F1E8"))
            name_ar = data.get("activity_name_ar", code_id)
            item = QListWidgetItem(f"{code_id}  —  {name_ar}\n{state.label_ar}")
            item.setData(Qt.UserRole, code_id)
            item.setForeground(QColor(color))
            item.setBackground(QColor(bg))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._list.addItem(item)

        total = len(active_codes)
        self._summary.setText(
            f"إجمالي الأكواد النشطة: {total}  |  "
            f"معتمد: {counts.get(STATUS_APPROVED, 0)}  |  "
            f"يحتاج مراجعة: {counts.get(STATUS_NEEDS_REVIEW, 0)}  |  "
            f"موجود غير معتمد: {counts.get(STATUS_PRESENT, 0)}  |  "
            f"بلا ملف: {counts.get(STATUS_NO_FILE, 0)}"
        )
        if self._list.count():
            self._list.setCurrentRow(0)

    def _on_selected(self, item: QListWidgetItem | None) -> None:
        if item is None:
            self._current_code = ""
            self._details.clear()
            self._set_action_state(False)
            return
        self._current_code = item.data(Qt.UserRole)
        self._render_details()

    def _render_details(self) -> None:
        code_id = self._current_code
        audit = self._audits.get(code_id)
        state = self._states.get(code_id)
        code = self._codes.get(code_id, {})
        if audit is None or state is None:
            self._details.clear()
            self._set_action_state(False)
            return

        issues = audit.issues
        issue_rows = "".join(
            f"<tr><td>{'خطأ' if issue.severity == 'error' else 'تحذير'}</td>"
            f"<td>{issue.message_ar}</td><td>{issue.suggestion_ar}</td></tr>"
            for issue in issues
        ) or "<tr><td colspan='3'>لا توجد ملاحظات جودة.</td></tr>"

        self._details.setHtml(f"""
        <html dir="rtl"><body style="font-family:Tajawal; color:#121B28; line-height:1.6;">
        <h2 style="color:#152433;">{code_id} — {code.get('activity_name_ar', code_id)}</h2>
        <table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse;">
          <tr style="background:#152433;color:#F5D48B;"><th>البند</th><th>القيمة</th></tr>
          <tr><td>حالة الاعتماد</td><td>{state.label_ar}</td></tr>
          <tr><td>مسار الملف</td><td style="direction:ltr;">{audit.path or 'لا يوجد'}</td></tr>
          <tr><td>الفقرات</td><td>{audit.paragraph_count}</td></tr>
          <tr><td>الجداول</td><td>{audit.table_count}</td></tr>
          <tr><td>الصور المضمنة</td><td>{audit.inline_image_count}</td></tr>
          <tr><td>المراجع</td><td>{state.reviewer or '-'}</td></tr>
          <tr><td>تاريخ الاعتماد</td><td>{state.approved_at or '-'}</td></tr>
          <tr><td>ملاحظات الاعتماد</td><td>{state.notes or '-'}</td></tr>
        </table>
        <h3 style="color:#152433;">ملاحظات الفحص</h3>
        <table width="100%" cellspacing="0" cellpadding="7" style="border-collapse:collapse;">
          <tr style="background:#152433;color:#F5D48B;"><th>النوع</th><th>الملاحظة</th><th>الإجراء</th></tr>
          {issue_rows}
        </table>
        </body></html>
        """)
        has_file = audit.exists and bool(audit.path)
        can_approve = has_file and not audit.issues
        self._open_btn.setEnabled(has_file)
        self._approve_btn.setEnabled(can_approve)
        self._review_btn.setEnabled(has_file)

    def _set_action_state(self, enabled: bool) -> None:
        self._open_btn.setEnabled(enabled)
        self._approve_btn.setEnabled(enabled)
        self._review_btn.setEnabled(enabled)

    def _open_current(self) -> None:
        audit = self._audits.get(self._current_code)
        if not audit or not audit.path:
            return
        path = Path(audit.path)
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "تعذر الفتح", str(exc))

    def _approve_current(self) -> None:
        audit = self._audits.get(self._current_code)
        if not audit or not audit.exists or audit.issues:
            return
        self._approval.approve(self._current_code, audit.path, reviewer="ATPAS", notes="اعتماد من مركز مكتبة Word")
        ActivityLog().append("اعتماد محتوى Word", {"code_id": self._current_code})
        QMessageBox.information(self, "تم الاعتماد", f"تم اعتماد محتوى {self._current_code}.")
        self._reload()

    def _mark_review_current(self) -> None:
        if not self._current_code:
            return
        self._approval.mark_needs_review(self._current_code, notes="إرجاع للمراجعة من مركز مكتبة Word")
        ActivityLog().append("إرجاع محتوى Word للمراجعة", {"code_id": self._current_code})
        QMessageBox.information(self, "تم", f"تم إرجاع {self._current_code} للمراجعة.")
        self._reload()

