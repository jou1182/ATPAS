#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feature 2 — Dynamic Template Variables (الحقول الديناميكية).

BuildVarsDialog: a modal RTL form shown before every build so the user can
fill in project-specific fields (project name, tender number, submission date,
contract value, engineer name).  The values returned by get_vars() are passed
as template_vars to Builder.build() and injected into the cover page.
"""

from __future__ import annotations

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui import theme


# ── Style constants ──────────────────────────────────────────────────────────

_NAVY   = theme.HEADER
_GOLD   = theme.ACCENT
_CREAM  = theme.SURFACE
_BORDER = theme.BORDER

_FIELD_STYLE = (
    "QLineEdit, QDateEdit {"
    f"  background: {_CREAM}; color: {_NAVY};"
    f"  border: 1.5px solid {_BORDER}; border-radius: 5px;"
    "  padding: 5px 8px; font-size: 13px;"
    "}"
    "QLineEdit:focus, QDateEdit:focus {"
    f"  border-color: {_GOLD};"
    "}"
)

_BTN_PRIMARY = (
    "QPushButton {"
    f"  background: {_NAVY}; color: {_GOLD};"
    "  border: none; border-radius: 6px;"
    "  padding: 8px 24px; font-size: 13px; font-weight: 700;"
    "}"
    f"QPushButton:hover {{ background: {theme.NAVY_MID}; }}"
    f"QPushButton:pressed {{ background: {theme.HEADER2}; }}"
)

_BTN_SECONDARY = (
    "QPushButton {"
    f"  background: {_CREAM}; color: {_NAVY};"
    f"  border: 1.5px solid {_NAVY}; border-radius: 6px;"
    "  padding: 8px 24px; font-size: 13px; font-weight: 700;"
    "}"
    f"QPushButton:hover {{ background: {theme.BG}; }}"
    f"QPushButton:pressed {{ background: {theme.BORDER}; }}"
)


# ── Dialog ───────────────────────────────────────────────────────────────────

class BuildVarsDialog(QDialog):
    """Modal form for collecting project-specific cover-page variables.

    Show before the build starts:

        dlg = BuildVarsDialog(project_id, owner_id, owner_name_ar, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return          # user cancelled
        template_vars = dlg.get_vars()
        # pass template_vars to BuildProgressDialog / Builder.build()

    All fields are optional — empty strings are returned for unfilled fields.
    """

    def __init__(
        self,
        project_id: str,
        owner_id: str,
        owner_name_ar: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._project_id   = project_id
        self._owner_id     = owner_id
        self._owner_name   = owner_name_ar

        self.setWindowTitle("بيانات العرض الفني")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setStyleSheet(f"background: {_CREAM}; color: {_NAVY};")

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title banner ────────────────────────────────────────────────
        banner = QWidget()
        banner.setStyleSheet(f"background: {_NAVY};")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(18, 14, 18, 14)

        title_lbl = QLabel("بيانات العرض الفني")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(f"color: {_GOLD};")
        title_lbl.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(title_lbl)

        subtitle_lbl = QLabel(
            f"الجهة: {self._owner_name}  |  المشروع: {self._project_id}"
        )
        subtitle_lbl.setStyleSheet("color: #AABBCC; font-size: 11px;")
        subtitle_lbl.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(subtitle_lbl)

        root.addWidget(banner)

        # ── Form body ───────────────────────────────────────────────────
        body = QWidget()
        body.setContentsMargins(0, 0, 0, 0)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 16)
        body_layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignRight)

        # Helper to make a labelled field
        def _label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {_NAVY}; font-weight: 600; font-size: 13px;")
            return lbl

        # 1. Project name
        self._project_name = QLineEdit()
        self._project_name.setPlaceholderText("اسم المشروع — يُستخدم تلقائياً إذا تُرك فارغاً")
        self._project_name.setStyleSheet(_FIELD_STYLE)
        form.addRow(_label("اسم المشروع"), self._project_name)

        # 2. Tender number
        self._tender_number = QLineEdit()
        self._tender_number.setPlaceholderText("مثال: MOH-2026-0041")
        self._tender_number.setStyleSheet(_FIELD_STYLE)
        form.addRow(_label("رقم المنافسة"), self._tender_number)

        # 3. Submission date
        self._submission_date = QDateEdit()
        self._submission_date.setCalendarPopup(True)
        self._submission_date.setDisplayFormat("yyyy-MM-dd")
        self._submission_date.setDate(QDate.currentDate())
        self._submission_date.setStyleSheet(_FIELD_STYLE)
        form.addRow(_label("تاريخ التقديم"), self._submission_date)

        # 4. Contract value
        self._contract_value = QLineEdit()
        self._contract_value.setPlaceholderText("مثال: 5,250,000 ريال")
        self._contract_value.setStyleSheet(_FIELD_STYLE)
        form.addRow(_label("قيمة العقد"), self._contract_value)

        # 5. Engineer name
        self._engineer_name = QLineEdit()
        self._engineer_name.setPlaceholderText("اسم المهندس المُعِد")
        self._engineer_name.setStyleSheet(_FIELD_STYLE)
        form.addRow(_label("اسم المهندس المُعِد"), self._engineer_name)

        body_layout.addLayout(form)

        # ── Hint ────────────────────────────────────────────────────────
        hint = QLabel("جميع الحقول اختيارية — القيم الفارغة تُستبدل بالقيم الافتراضية")
        hint.setStyleSheet("color: #7A8B9C; font-size: 10px;")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        body_layout.addWidget(hint)

        # ── Action buttons ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._cancel_btn = QPushButton("إلغاء")
        self._cancel_btn.setStyleSheet(_BTN_SECONDARY)
        self._cancel_btn.clicked.connect(self.reject)

        self._build_btn = QPushButton("بناء العرض")
        self._build_btn.setStyleSheet(_BTN_PRIMARY)
        self._build_btn.setDefault(True)
        self._build_btn.clicked.connect(self.accept)

        btn_row.addWidget(self._cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._build_btn)

        body_layout.addLayout(btn_row)
        root.addWidget(body)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_vars(self) -> dict[str, str]:
        """Return a dict of template variable values.

        Empty strings are returned for fields the user left blank.
        The caller should pass this dict to Builder.build(template_vars=...).
        """
        return {
            "project_name":    self._project_name.text().strip(),
            "tender_number":   self._tender_number.text().strip(),
            "submission_date": self._submission_date.date().toString("yyyy-MM-dd"),
            "contract_value":  self._contract_value.text().strip(),
            "engineer_name":   self._engineer_name.text().strip(),
        }
