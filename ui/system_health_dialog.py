#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Arabic system health dialog for ATPAS."""

from __future__ import annotations

import html
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from utils.activity_log import ActivityLog
from utils.system_health import (
    HealthIssue,
    SystemHealthReport,
    render_html_report,
    save_html_report,
    save_system_health_report,
)


class SystemHealthDialog(QDialog):
    """Show a readable, actionable health report for non-technical users."""

    def __init__(self, report: SystemHealthReport, parent=None) -> None:
        super().__init__(parent)
        self._report = report
        self.setWindowTitle("صحة النظام")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(760, 620)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        title = QLabel("تقرير صحة النظام")
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setStyleSheet(
            "font-size: 18px; font-weight: 900; color: #152433; "
            "padding-bottom: 7px; border-bottom: 2px solid #C9921B;"
        )
        root.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        cards.addWidget(self._metric_card("درجة الجاهزية", f"{self._report.score}%", theme.HEADER))
        cards.addWidget(self._metric_card("الحالة", self._report.status_ar, self._status_color()))
        cards.addWidget(self._metric_card("أخطاء", str(len(self._report.errors)), theme.ERROR))
        cards.addWidget(self._metric_card("تحذيرات", str(len(self._report.warnings)), theme.WARNING))
        root.addLayout(cards)

        self._browser = QTextBrowser(self)
        self._browser.setLayoutDirection(Qt.RightToLeft)
        self._browser.setOpenExternalLinks(False)
        self._browser.setHtml(self._render_html())
        root.addWidget(self._browser, stretch=1)

        actions = QHBoxLayout()
        copy_btn = QPushButton("نسخ التقرير")
        copy_btn.clicked.connect(self._copy_report)
        export_btn = QPushButton("تصدير Markdown")
        export_btn.clicked.connect(self._export_report)
        html_btn = QPushButton("تصدير HTML")
        html_btn.clicked.connect(self._export_html_report)
        pdf_btn = QPushButton("تصدير PDF")
        pdf_btn.clicked.connect(self._export_pdf_report)
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        actions.addWidget(copy_btn)
        actions.addWidget(export_btn)
        actions.addWidget(html_btn)
        actions.addWidget(pdf_btn)
        actions.addStretch()
        actions.addWidget(close_btn)
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
                min-width: 110px;
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
            """
        )

    def _metric_card(self, label: str, value: str, color: str) -> QWidget:
        card = QWidget(self)
        card.setObjectName("healthCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        label_w = QLabel(label)
        label_w.setAlignment(Qt.AlignCenter)
        label_w.setStyleSheet(f"color: {theme.TEXT2}; font-size: 11px; font-weight: 700;")

        value_w = QLabel(value)
        value_w.setAlignment(Qt.AlignCenter)
        value_w.setWordWrap(True)
        value_w.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 900;")

        layout.addWidget(label_w)
        layout.addWidget(value_w)
        card.setStyleSheet(
            """
            QWidget#healthCard {
                background: #FEFCF7;
                border: 1px solid #D5CFBF;
                border-top: 3px solid %s;
                border-radius: 10px;
            }
            """ % color
        )
        return card

    def _status_color(self) -> str:
        if self._report.errors:
            return theme.ERROR
        if self._report.warnings:
            return theme.WARNING
        return theme.SUCCESS

    def _render_html(self) -> str:
        r = self._report
        return f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
          <meta charset="utf-8">
          <style>
            body {{
              font-family: 'Tajawal';
              color: #121B28;
              direction: rtl;
              text-align: right;
              margin: 8px 10px;
              line-height: 1.55;
            }}
            h2 {{
              color: #152433;
              margin: 12px 0 8px 0;
              padding-bottom: 5px;
              border-bottom: 1px solid #D5CFBF;
              font-size: 16px;
            }}
            table {{
              width: 100%;
              border-collapse: collapse;
              margin: 8px 0 14px 0;
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
            .ok {{ color: {theme.SUCCESS}; font-weight: 800; }}
            .error {{ color: {theme.ERROR}; font-weight: 800; }}
            .warning {{ color: {theme.WARNING}; font-weight: 800; }}
            .info {{ color: {theme.INFO}; font-weight: 800; }}
            .empty {{
              background: {theme.SUCCESS_PALE};
              border-right: 4px solid {theme.SUCCESS};
              padding: 10px 12px;
              border-radius: 8px;
              margin: 10px 0;
            }}
            .path {{
              direction: ltr;
              unicode-bidi: embed;
              font-family: Tajawal;
              display: inline-block;
            }}
          </style>
        </head>
        <body>
          <h2>ملخص سريع</h2>
          <table>
            <tr><th>البند</th><th>القيمة</th></tr>
            <tr><td>الأكواد الكلية</td><td>{r.total_codes}</td></tr>
            <tr><td>الأكواد النشطة</td><td>{r.active_codes}</td></tr>
            <tr><td>الأكواد غير النشطة</td><td>{r.inactive_codes}</td></tr>
            <tr><td>المشاريع</td><td>{r.projects_count}</td></tr>
            <tr><td>الجهات المالكة</td><td>{r.owners_count}</td></tr>
            <tr><td>الأنماط الجاهزة</td><td>{r.presets_count}</td></tr>
            <tr><td>ملفات Word الموجودة</td><td>{r.source_documents_count}</td></tr>
            <tr><td>الأكواد المرتبطة بمحتوى Word</td><td>{r.linked_documents_count}</td></tr>
            <tr><td>أكواد بلا ملف Word مطابق</td><td>{r.missing_documents_count}</td></tr>
            <tr><td>ملفات Word المفحوصة</td><td>{r.checked_word_documents_count}</td></tr>
            <tr><td>ملاحظات جودة محتوى Word</td><td>{r.word_content_issue_count}</td></tr>
            <tr><td>خط الإخراج الإجباري</td><td>{html.escape(r.output_font_family)}</td></tr>
            <tr><td>عقد الإخراج</td><td>{html.escape(r.output_contract_status_ar)}</td></tr>
          </table>

          <h2>المشاكل والإجراءات المقترحة</h2>
          {self._render_issues()}
        </body>
        </html>
        """

    def _render_issues(self) -> str:
        if not self._report.issues:
            return """
            <div class="empty">
              <span class="ok">النظام سليم.</span>
              لا توجد أخطاء أو تحذيرات حالية. يمكنك بناء العروض بثقة.
            </div>
            """

        rows = []
        for issue in self._report.issues:
            rows.append(
                "<tr>"
                f"<td>{_severity_label(issue)}</td>"
                f"<td>{html.escape(issue.scope)}</td>"
                f"<td>{html.escape(issue.message_ar)}</td>"
                f"<td>{html.escape(issue.suggestion_ar or 'راجع الملف المشار إليه.')}</td>"
                "</tr>"
            )
        return (
            "<table>"
            "<tr><th>النوع</th><th>المكان</th><th>الملاحظة</th><th>الإجراء المقترح</th></tr>"
            + "".join(rows)
            + "</table>"
        )

    def _copy_report(self) -> None:
        QApplication.clipboard().setText(_plain_text_report(self._report))

    def _export_report(self) -> None:
        default_path = Path.home() / "Desktop" / "ATPAS_Health_Report.md"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير تقرير صحة النظام",
            str(default_path),
            "Markdown Files (*.md);;All Files (*)",
        )
        if not path:
            return

        try:
            saved_path = save_system_health_report(self._report, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "تعذّر التصدير", f"تعذّر حفظ التقرير:\n{exc}")
            return

        QMessageBox.information(
            self,
            "تم التصدير",
            f"تم حفظ تقرير صحة النظام بنجاح:\n{saved_path}",
        )
        ActivityLog().append("تصدير تقرير صحة النظام Markdown", {"path": str(saved_path)})

    def _export_html_report(self) -> None:
        default_path = Path.home() / "Desktop" / "ATPAS_Health_Report.html"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير تقرير صحة النظام HTML",
            str(default_path),
            "HTML Files (*.html);;All Files (*)",
        )
        if not path:
            return

        try:
            saved_path = save_html_report(self._report, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "تعذّر التصدير", f"تعذّر حفظ التقرير:\n{exc}")
            return

        QMessageBox.information(self, "تم التصدير", f"تم حفظ تقرير HTML:\n{saved_path}")
        ActivityLog().append("تصدير تقرير صحة النظام HTML", {"path": str(saved_path)})

    def _export_pdf_report(self) -> None:
        default_path = Path.home() / "Desktop" / "ATPAS_Health_Report.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير تقرير صحة النظام PDF",
            str(default_path),
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not path:
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            doc = QTextDocument()
            doc.setHtml(render_html_report(self._report))
            doc.print_(printer)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "تعذّر التصدير", f"تعذّر إنشاء ملف PDF:\n{exc}")
            return

        QMessageBox.information(self, "تم التصدير", f"تم حفظ تقرير PDF:\n{path}")
        ActivityLog().append("تصدير تقرير صحة النظام PDF", {"path": str(path)})


def _severity_label(issue: HealthIssue) -> str:
    labels = {
        "error": '<span class="error">خطأ</span>',
        "warning": '<span class="warning">تحذير</span>',
        "info": '<span class="info">معلومة</span>',
    }
    return labels.get(issue.severity, html.escape(issue.severity))


def _plain_text_report(report: SystemHealthReport) -> str:
    lines = [
        "تقرير صحة نظام ATPAS",
        f"درجة الجاهزية: {report.score}%",
        f"الحالة: {report.status_ar}",
        f"الأكواد: {report.active_codes} نشط من أصل {report.total_codes}",
        f"المشاريع: {report.projects_count}",
        f"الجهات المالكة: {report.owners_count}",
        f"الأنماط الجاهزة: {report.presets_count}",
        f"ملفات Word الموجودة: {report.source_documents_count}",
        f"أكواد بلا ملف Word مطابق: {report.missing_documents_count}",
        f"ملفات Word المفحوصة: {report.checked_word_documents_count}",
        f"ملاحظات جودة محتوى Word: {report.word_content_issue_count}",
        f"خط الإخراج الإجباري: {report.output_font_family}",
        f"عقد الإخراج: {report.output_contract_status_ar}",
        "",
        "الملاحظات:",
    ]
    if not report.issues:
        lines.append("- لا توجد ملاحظات.")
    for issue in report.issues:
        lines.append(f"- [{issue.severity}] {issue.scope}: {issue.message_ar}")
        if issue.suggestion_ar:
            lines.append(f"  الإجراء: {issue.suggestion_ar}")
    return "\n".join(lines)
