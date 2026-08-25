#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة "عن النظام" — ATPAS About Dialog
========================================
تعرض: الإصدار • حالة الترخيص • تاريخ الانتهاء • Hardware ID • الدعم
"""

from __future__ import annotations

import webbrowser
import urllib.parse
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ui import theme


# ── رسم المربع المستدير الملوّن ─────────────────────────────────────────────
def _card(bg: str, border: str = "") -> str:
    b = f"border: 1.5px solid {border};" if border else ""
    return f"background:{bg}; border-radius:8px; {b}"


class AboutDialog(QDialog):
    """نافذة 'عن نظام ATPAS' — إصدار، ترخيص، HW ID، دعم."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("عن نظام ATPAS")
        self.setFixedWidth(500)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    # ── بناء الواجهة ─────────────────────────────────────────────────────────

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_body())

    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {theme.NAVY_MID}, stop:1 {theme.HEADER2});
            border-bottom: 4px solid {theme.ACCENT};
        """)
        lay = QVBoxLayout(hdr)
        lay.setContentsMargins(28, 20, 28, 16)
        lay.setSpacing(4)

        # اسم النظام
        t = QLabel("نظام بناء العروض الفنية")
        t.setStyleSheet("color:#FFF; font-size:20px; font-weight:800; background:transparent;")
        t.setAlignment(Qt.AlignRight)

        # اسم الشركة
        brand = QLabel("الرواف للهندسة والتقنية  |  Al-Rawaf Engineering")
        brand.setStyleSheet(f"color:{theme.ACCENT}; font-size:12px; font-weight:600; background:transparent;")
        brand.setLayoutDirection(Qt.LeftToRight)
        brand.setAlignment(Qt.AlignLeft)

        # شارة الإصدار
        ver = self._get_version()
        ver_lbl = QLabel(f"ATPAS  {ver}")
        ver_lbl.setStyleSheet(f"""
            color:{theme.HEADER}; background:{theme.ACCENT};
            font-size:11px; font-weight:800;
            padding:4px 14px; border-radius:5px;
        """)
        ver_lbl.setAlignment(Qt.AlignCenter)

        row = QHBoxLayout()
        row.addWidget(ver_lbl)
        row.addStretch()

        lay.addWidget(t)
        lay.addWidget(brand)
        lay.addSpacing(6)
        lay.addLayout(row)

        return hdr

    def _make_body(self) -> QWidget:
        body = QWidget()
        body.setStyleSheet("background:#F5F7FA;")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # ── حالة الترخيص ─────────────────────────────────────────────────
        lic = self._get_license_info()
        lay.addWidget(self._make_license_card(lic))

        # ── Hardware ID ───────────────────────────────────────────────────
        lay.addWidget(self._make_hw_card(lic.get("hardware_id", "—")))

        # ── الدعم الفني ───────────────────────────────────────────────────
        lay.addWidget(self._make_support_card(lic))

        # ── زر الإغلاق ───────────────────────────────────────────────────
        close_btn = QPushButton("إغلاق")
        close_btn.setFixedHeight(42)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background:{theme.NAVY_MID}; color:#FFF;
                font-size:13px; font-weight:700;
                border:none; border-radius:8px;
            }}
            QPushButton:hover   {{ background:#2A4A63; }}
            QPushButton:pressed {{ background:{theme.HEADER}; }}
        """)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

        return body

    # ── بطاقة حالة الترخيص ───────────────────────────────────────────────────

    def _make_license_card(self, lic: dict) -> QWidget:
        valid     = lic.get("valid", False)
        days_left = lic.get("days_left")
        expiry    = lic.get("expiry")

        if valid:
            if days_left is not None and days_left <= 7:
                bg, border, icon = "#FFF8E1", "#E8A020", "⚠️"
                status_text = f"ينتهي خلال {days_left} يوم"
                color = "#8B5E00"
            else:
                bg, border, icon = "#EAF7EF", "#2E7D52", "✅"
                status_text = f"مفعّل — {days_left} يوم متبقية" if days_left else "مفعّل"
                color = "#1B5E36"
        else:
            bg, border, icon = "#FDECEA", theme.DEV_RED, "❌"
            status_text = lic.get("message", "غير مفعّل")
            color = "#B71C1C"

        card = QFrame()
        card.setStyleSheet(f"background:{bg}; border:1.5px solid {border}; border-radius:8px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        title = QLabel(f"{icon}  حالة الترخيص")
        title.setStyleSheet(f"color:{color}; font-size:12px; font-weight:800; background:transparent;")
        title.setAlignment(Qt.AlignRight)
        lay.addWidget(title)

        status_lbl = QLabel(status_text)
        status_lbl.setStyleSheet(f"color:{color}; font-size:13px; font-weight:700; background:transparent;")
        status_lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(status_lbl)

        if expiry:
            exp_str = expiry if isinstance(expiry, str) else expiry.strftime("%Y-%m-%d")
            exp_lbl = QLabel(f"تاريخ الانتهاء: {exp_str}")
            exp_lbl.setStyleSheet(f"color:{color}; font-size:11px; background:transparent;")
            exp_lbl.setAlignment(Qt.AlignRight)
            lay.addWidget(exp_lbl)

        return card

    # ── بطاقة Hardware ID ────────────────────────────────────────────────────

    def _make_hw_card(self, hw_id: str) -> QWidget:
        card = QFrame()
        card.setStyleSheet("background:#FFFFFF; border:1.5px solid #D0D7E3; border-radius:8px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        lbl = QLabel("💻  معرّف الجهاز (Hardware ID)")
        lbl.setStyleSheet(f"color:{theme.NAVY_MID}; font-size:12px; font-weight:800; background:transparent;")
        lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._hw_field = QLineEdit(hw_id)
        self._hw_field.setReadOnly(True)
        self._hw_field.setAlignment(Qt.AlignCenter)
        self._hw_field.setFont(QFont("Tajawal", 13))
        self._hw_field.setFixedHeight(38)
        self._hw_field.setStyleSheet(f"""
            QLineEdit {{
                background:#F0F4FA; border:1.5px solid #B0BEC5;
                border-radius:6px; padding:0 10px;
                color:{theme.NAVY_MID}; font-weight:700; letter-spacing:1px;
            }}
        """)

        copy_btn = QPushButton("📋 نسخ")
        copy_btn.setFixedSize(80, 38)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background:{theme.NAVY_MID}; color:#FFF;
                font-size:12px; font-weight:700;
                border:none; border-radius:6px;
            }}
            QPushButton:hover   {{ background:#2A4A63; }}
            QPushButton:pressed {{ background:{theme.HEADER}; }}
        """)
        self._copy_hw_btn = copy_btn

        copy_btn.clicked.connect(self._copy_hw_id)

        # يمين ← نسخ | يسار ← الحقل
        row.addWidget(copy_btn)
        row.addWidget(self._hw_field, stretch=1)
        lay.addLayout(row)

        note = QLabel("أرسل هذا الرقم للمطوّر لتفعيل ترخيصك أو تجديده")
        note.setStyleSheet("color:#607D8B; font-size:10px; background:transparent;")
        note.setAlignment(Qt.AlignRight)
        lay.addWidget(note)

        return card

    # ── بطاقة الدعم الفني ────────────────────────────────────────────────────

    def _make_support_card(self, lic: dict) -> QWidget:
        card = QFrame()
        card.setStyleSheet("background:#FFFFFF; border:1.5px solid #D0D7E3; border-radius:8px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        lbl = QLabel("📞  الدعم الفني")
        lbl.setStyleSheet(f"color:{theme.NAVY_MID}; font-size:12px; font-weight:800; background:transparent;")
        lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(lbl)

        info = QLabel("📧  jou1182@gmail.com   |   الرواف للهندسة والتقنية")
        info.setStyleSheet("color:#455A64; font-size:12px; background:transparent;")
        info.setAlignment(Qt.AlignRight)
        lay.addWidget(info)

        # زر طلب التجديد عبر واتساب
        hw_id     = lic.get("hardware_id", "—")
        days_left = lic.get("days_left")
        expiry    = lic.get("expiry", "")
        if isinstance(expiry, datetime):
            expiry = expiry.strftime("%Y-%m-%d")

        wa_btn = QPushButton("💬  أرسل طلب تجديد عبر واتساب")
        wa_btn.setFixedHeight(40)
        wa_btn.setCursor(Qt.PointingHandCursor)
        wa_btn.setStyleSheet("""
            QPushButton {
                background:#25D366; color:#FFF;
                font-size:13px; font-weight:700;
                border:none; border-radius:7px;
            }
            QPushButton:hover   { background:#1DB354; }
            QPushButton:pressed { background:#178A42; }
        """)
        wa_btn.clicked.connect(
            lambda: self._send_renewal_request(hw_id, days_left, expiry)
        )
        lay.addWidget(wa_btn)

        return card

    # ── المنطق ───────────────────────────────────────────────────────────────

    def _get_version(self) -> str:
        try:
            v = QApplication.applicationVersion()
            return f"v{v}" if v else "v—"
        except Exception:
            return "v—"

    def _get_license_info(self) -> dict:
        try:
            from utils.license_manager import get_license_info
            return get_license_info()
        except Exception:
            return {"valid": False, "message": "تعذّر قراءة الترخيص", "days_left": None, "hardware_id": "—"}

    def _copy_hw_id(self) -> None:
        QApplication.clipboard().setText(self._hw_field.text())
        orig = self._copy_hw_btn.text()
        self._copy_hw_btn.setText("✅ تم النسخ")
        QTimer.singleShot(1800, lambda: self._copy_hw_btn.setText(orig))

    def _send_renewal_request(
        self, hw_id: str, days_left: Optional[int], expiry: str
    ) -> None:
        days_str = f"متبقٍّ {days_left} يوم" if days_left else "الترخيص منتهٍ"
        msg = (
            f"السلام عليكم،\n\n"
            f"أرغب في تجديد ترخيص نظام ATPAS.\n\n"
            f"معرّف الجهاز (Hardware ID):\n{hw_id}\n\n"
            f"حالة الترخيص الحالية: {days_str}\n"
            f"تاريخ الانتهاء: {expiry}\n\n"
            f"يرجى إرسال كود التجديد المناسب.\n\n"
            f"شكراً"
        )
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(msg)}")
