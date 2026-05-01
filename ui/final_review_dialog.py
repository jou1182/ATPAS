#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Final pre-build review dialog for ATPAS proposals."""

from __future__ import annotations

import html
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from utils.proposal_comparison import ProposalComparison
from utils.proposal_readiness import ProposalReadiness
from utils.word_content_audit import WordContentAudit, flatten_issues


class FinalReviewDialog(QDialog):
    """One-page decision checkpoint before Builder starts."""

    def __init__(
        self,
        *,
        readiness: ProposalReadiness,
        codes: dict[str, dict[str, Any]],
        project_label: str,
        owner_label: str,
        comparison: ProposalComparison,
        content_audits: list[WordContentAudit],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._readiness = readiness
        self._codes = codes
        self._project_label = project_label
        self._owner_label = owner_label
        self._comparison = comparison
        self._content_audits = content_audits

        self.setWindowTitle("الاعتماد النهائي قبل البناء")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(820, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("الاعتماد النهائي قبل بناء العرض")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #152433; "
            "padding-bottom: 7px; border-bottom: 2px solid #C9921B;"
        )
        root.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        cards.addWidget(self._metric_card("قرار الجاهزية", self._readiness.decision_ar, self._decision_color()))
        cards.addWidget(self._metric_card("الأكواد النهائية", str(len(self._readiness.resolved_codes)), "#152433"))
        cards.addWidget(self._metric_card("التبعيات المضافة", str(len(self._readiness.dependency_codes)), "#1C5D85"))
        cards.addWidget(self._metric_card("الصفحات التقديرية", str(self._readiness.total_pages), "#2B7549"))
        root.addLayout(cards)

        self._browser = QTextBrowser(self)
        self._browser.setLayoutDirection(Qt.RightToLeft)
        self._browser.setHtml(self._render_html())
        root.addWidget(self._browser, stretch=1)

        actions = QHBoxLayout()
        cancel_btn = QPushButton("رجوع للمراجعة")
        cancel_btn.clicked.connect(self.reject)
        build_btn = QPushButton("اعتمد وابن العرض")
        build_btn.setEnabled(self._readiness.can_build)
        build_btn.setDefault(True)
        build_btn.clicked.connect(self.accept)
        actions.addWidget(cancel_btn)
        actions.addStretch()
        actions.addWidget(build_btn)
        root.addLayout(actions)

        self.setStyleSheet(
            """
            QDialog {
                background: #FEFCF7;
                color: #121B28;
            }
            QTextBrowser {
                background: #FFFFFF;
                border: 1px solid #D5CFBF;
                border-radius: 10px;
                padding: 8px;
                color: #121B28;
            }
            QPushButton {
                min-width: 130px;
                padding: 8px 18px;
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
            QPushButton:default {
                background: #2B7549;
                color: #FFFFFF;
                border: none;
            }
            QPushButton:disabled {
                background: #EDEAE4;
                color: #9B9B9B;
            }
            """
        )

    def _metric_card(self, label: str, value: str, color: str) -> QWidget:
        card = QWidget(self)
        card.setObjectName("finalReviewCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        label_w = QLabel(label)
        label_w.setAlignment(Qt.AlignCenter)
        label_w.setStyleSheet("color: #5A6B7C; font-size: 11px; font-weight: 700;")

        value_w = QLabel(value)
        value_w.setAlignment(Qt.AlignCenter)
        value_w.setWordWrap(True)
        value_w.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900;")

        layout.addWidget(label_w)
        layout.addWidget(value_w)
        card.setStyleSheet(
            """
            QWidget#finalReviewCard {
                background: #FAF0DC;
                border: 1px solid #D5CFBF;
                border-radius: 10px;
            }
            """
        )
        return card

    def _decision_color(self) -> str:
        if self._readiness.decision == "blocked":
            return "#B03030"
        if self._readiness.decision == "caution":
            return "#B56618"
        return "#2B7549"

    def _render_html(self) -> str:
        return f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
          <meta charset="utf-8">
          <style>
            body {{
              font-family: Tajawal;
              color: #121B28;
              direction: rtl;
              text-align: right;
              line-height: 1.58;
              margin: 8px 10px;
            }}
            h2 {{
              color: #152433;
              margin: 13px 0 8px;
              padding-bottom: 5px;
              border-bottom: 1px solid #D5CFBF;
              font-size: 15px;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
              margin: 8px 0 14px;
            }}
            th {{
              background: #152433;
              color: #F5D48B;
              padding: 8px;
              font-weight: 800;
            }}
            td {{
              border-bottom: 1px solid #ECE3D2;
              padding: 7px 8px;
              vertical-align: top;
            }}
            .decision {{
              background: {self._decision_bg()};
              border-right: 5px solid {self._decision_color()};
              border-radius: 8px;
              padding: 10px 12px;
              font-weight: 800;
              color: {self._decision_color()};
            }}
            .muted {{ color: #5A6B7C; }}
            .ltr {{
              direction: ltr;
              unicode-bidi: embed;
              font-family: Tajawal;
            }}
          </style>
        </head>
        <body>
          <div class="decision">
            {html.escape(self._readiness.decision_ar)} - {html.escape(self._readiness.decision_reason_ar)}
          </div>

          <h2>بيانات العرض</h2>
          <table>
            <tr><th>البند</th><th>القيمة</th></tr>
            <tr><td>المشروع</td><td>{html.escape(self._project_label)}</td></tr>
            <tr><td>الجهة المالكة</td><td>{html.escape(self._owner_label)}</td></tr>
            <tr><td>الأكواد المختارة يدويًا</td><td>{len(self._readiness.selected_codes)}</td></tr>
            <tr><td>الأكواد النهائية بعد التبعيات</td><td>{len(self._readiness.resolved_codes)}</td></tr>
            <tr><td>الصفحات التقديرية</td><td>{self._readiness.total_pages}</td></tr>
          </table>

          {self._render_blockers()}
          {self._render_cautions()}
          {self._render_phase_coverage()}
          {self._render_comparison()}
          {self._render_dependencies()}
          {self._render_content_notes()}
          {self._render_final_codes()}
        </body>
        </html>
        """

    def _decision_bg(self) -> str:
        if self._readiness.decision == "blocked":
            return "#FDEEEE"
        if self._readiness.decision == "caution":
            return "#FFF4E7"
        return "#EAF5EF"

    def _render_blockers(self) -> str:
        if not self._readiness.blockers:
            return ""
        items = "".join(f"<li>{html.escape(item)}</li>" for item in self._readiness.blockers)
        return f"<h2>موانع البناء</h2><ul>{items}</ul>"

    def _render_cautions(self) -> str:
        if not self._readiness.cautions:
            return "<h2>الملاحظات</h2><p class='muted'>لا توجد تحفظات حالية.</p>"
        items = "".join(f"<li>{html.escape(item)}</li>" for item in self._readiness.cautions)
        return f"<h2>الملاحظات التي تعتمدها قبل البناء</h2><ul>{items}</ul>"

    def _render_phase_coverage(self) -> str:
        rows = []
        for phase in self._readiness.phase_coverage:
            status = "مغطاة" if phase.covered else "غير ممثلة"
            rows.append(
                "<tr>"
                f"<td>{html.escape(phase.name_ar)}</td>"
                f"<td>{status}</td>"
                f"<td>{phase.code_count}</td>"
                f"<td>{phase.page_count}</td>"
                "</tr>"
            )
        return (
            "<h2>مصفوفة تغطية مراحل المشروع</h2>"
            "<table><tr><th>المرحلة</th><th>الحالة</th><th>الأكواد</th><th>الصفحات</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _render_comparison(self) -> str:
        if not self._comparison.has_previous:
            return (
                "<h2>المقارنة مع آخر عرض مشابه</h2>"
                "<p class='muted'>لا يوجد عرض سابق بنفس المشروع والجهة في سجل الإصدارات.</p>"
            )

        added = ", ".join(self._comparison.added_codes) or "لا يوجد"
        removed = ", ".join(self._comparison.removed_codes) or "لا يوجد"
        return (
            "<h2>المقارنة مع آخر عرض مشابه</h2>"
            "<table><tr><th>البند</th><th>القيمة</th></tr>"
            f"<tr><td>العرض السابق</td><td>{html.escape(self._comparison.previous_label)}</td></tr>"
            f"<tr><td>تاريخ العرض السابق</td><td>{html.escape(self._comparison.previous_timestamp)}</td></tr>"
            f"<tr><td>أكواد مضافة</td><td class='ltr'>{html.escape(added)}</td></tr>"
            f"<tr><td>أكواد محذوفة</td><td class='ltr'>{html.escape(removed)}</td></tr>"
            f"<tr><td>أكواد مشتركة</td><td>{len(self._comparison.shared_codes)}</td></tr>"
            f"<tr><td>فرق الصفحات</td><td>{self._comparison.page_delta:+d}</td></tr>"
            "</table>"
        )

    def _render_dependencies(self) -> str:
        if not self._readiness.dependency_codes:
            return "<h2>التبعيات الهندسية</h2><p class='muted'>لا توجد تبعيات إضافية.</p>"
        rows = []
        for code_id in self._readiness.dependency_codes:
            code = self._codes.get(code_id, {})
            rows.append(
                "<tr>"
                f"<td class='ltr'>{html.escape(code_id)}</td>"
                f"<td>{html.escape(str(code.get('activity_name_ar', code_id)))}</td>"
                "</tr>"
            )
        return (
            "<h2>أكواد ستضاف تلقائيًا بسبب التبعيات</h2>"
            "<table><tr><th>الكود</th><th>النشاط</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _render_content_notes(self) -> str:
        issues = flatten_issues(self._content_audits)
        if not issues:
            return "<h2>محتوى Word</h2><p class='muted'>لا توجد ملاحظات محتوى.</p>"
        rows = []
        for issue in issues[:20]:
            rows.append(
                "<tr>"
                f"<td>{'خطأ' if issue.severity == 'error' else 'تحذير'}</td>"
                f"<td class='ltr'>{html.escape(issue.code_id)}</td>"
                f"<td>{html.escape(issue.message_ar)}</td>"
                "</tr>"
            )
        more = ""
        if len(issues) > 20:
            more = f"<p class='muted'>و{len(issues) - 20} ملاحظة أخرى.</p>"
        return (
            "<h2>ملاحظات محتوى Word</h2>"
            "<table><tr><th>النوع</th><th>الكود</th><th>الملاحظة</th></tr>"
            + "".join(rows)
            + "</table>"
            + more
        )

    def _render_final_codes(self) -> str:
        rows = []
        for idx, code_id in enumerate(self._readiness.resolved_codes, 1):
            code = self._codes.get(code_id, {})
            rows.append(
                "<tr>"
                f"<td>{idx}</td>"
                f"<td class='ltr'>{html.escape(code_id)}</td>"
                f"<td>{html.escape(str(code.get('activity_name_ar', code_id)))}</td>"
                f"<td>{html.escape(str(code.get('category', '')))}</td>"
                "</tr>"
            )
        return (
            "<h2>الهيكل النهائي للأكواد</h2>"
            "<table><tr><th>م</th><th>الكود</th><th>النشاط</th><th>الفئة</th></tr>"
            + "".join(rows)
            + "</table>"
        )

