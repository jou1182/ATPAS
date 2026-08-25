#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة تحذير انتهاء الترخيص — Expiry Warning Dialog
=====================================================
تعرض: أيام متبقية • Hardware ID قابل للنسخ • زر طلب التجديد عبر واتساب
"""

from __future__ import annotations

import urllib.parse
import webbrowser

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from ui import theme


class ExpiryWarningDialog(QDialog):
    """
    نافذة تحذير ذكية عند اقتراب انتهاء الترخيص.
    تتضمن Hardware ID مع زر نسخ + زر طلب تجديد مباشر عبر واتساب.
    """

    def __init__(
        self,
        days_left: int,
        expiry_date: str = "",
        hardware_id: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("تنبيه — انتهاء الترخيص قريباً")
        self.setFixedWidth(480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)
        self._days_left   = days_left
        self._expiry_date = expiry_date
        self._hw_id       = hardware_id
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
        # أحمر داكن للتحذير
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #7B1010, stop:1 #4E0A0A);
            border-bottom: 4px solid #E8A020;
        """)
        lay = QVBoxLayout(hdr)
        lay.setContentsMargins(28, 18, 28, 14)
        lay.setSpacing(4)

        days_str = f"{self._days_left} يوم" if self._days_left > 1 else "يوم واحد"

        title = QLabel(f"⚠️  ترخيصك ينتهي خلال {days_str}!")
        title.setStyleSheet(
            "color:#FFF; font-size:18px; font-weight:800; background:transparent;"
        )
        title.setAlignment(Qt.AlignRight)
        lay.addWidget(title)

        if self._expiry_date:
            sub = QLabel(f"تاريخ الانتهاء: {self._expiry_date}")
            sub.setStyleSheet(
                "color:#FFCC80; font-size:12px; background:transparent;"
            )
            sub.setAlignment(Qt.AlignRight)
            lay.addWidget(sub)

        return hdr

    def _make_body(self) -> QWidget:
        body = QWidget()
        body.setStyleSheet("background:#FFF8F8;")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # ── رسالة التحذير ────────────────────────────────────────────────
        msg_lbl = QLabel(
            "جدّد ترخيصك الآن لتجنّب انقطاع الخدمة.\n"
            "انسخ معرّف جهازك وأرسله للمطوّر لاستلام كود التجديد."
        )
        msg_lbl.setStyleSheet(
            "color:#4A0000; font-size:12px; background:transparent; line-height:1.6;"
        )
        msg_lbl.setAlignment(Qt.AlignRight)
        msg_lbl.setWordWrap(True)
        lay.addWidget(msg_lbl)

        # ── Hardware ID ───────────────────────────────────────────────────
        lay.addWidget(self._make_hw_section())

        # ── أزرار الإجراء ─────────────────────────────────────────────────
        lay.addWidget(self._make_actions())

        return body

    def _make_hw_section(self) -> QWidget:
        frame = QFrame()
        frame.setStyleSheet(
            "background:#FFF; border:1.5px solid #FFAB91; border-radius:8px;"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lbl = QLabel("💻  معرّف جهازك (Hardware ID) — أرسله للمطوّر:")
        lbl.setStyleSheet(
            "color:#4A0000; font-size:11px; font-weight:700; background:transparent;"
        )
        lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._hw_field = QLineEdit(self._hw_id or "—")
        self._hw_field.setReadOnly(True)
        self._hw_field.setAlignment(Qt.AlignCenter)
        self._hw_field.setFixedHeight(38)
        self._hw_field.setStyleSheet("""
            QLineEdit {
                font-family:'Tajawal';
                font-size:14px; font-weight:700; letter-spacing:1px;
                background:#FFF9F0; border:1.5px solid #FFAB91;
                border-radius:6px; padding:0 10px; color:#4A0000;
            }
        """)

        self._copy_btn = QPushButton("📋 نسخ")
        self._copy_btn.setFixedSize(80, 38)
        self._copy_btn.setCursor(Qt.PointingHandCursor)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background:#7B1010; color:#FFF;
                font-size:12px; font-weight:700;
                border:none; border-radius:6px;
            }
            QPushButton:hover   { background:#9B2020; }
            QPushButton:pressed { background:#5A0A0A; }
        """)
        self._copy_btn.clicked.connect(self._copy_hw)

        row.addWidget(self._copy_btn)
        row.addWidget(self._hw_field, stretch=1)
        lay.addLayout(row)

        return frame

    def _make_actions(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # زر واتساب — الأبرز
        wa_btn = QPushButton("💬  أرسل طلب التجديد عبر واتساب الآن")
        wa_btn.setFixedHeight(46)
        wa_btn.setCursor(Qt.PointingHandCursor)
        wa_btn.setStyleSheet("""
            QPushButton {
                background:#25D366; color:#FFF;
                font-size:14px; font-weight:800;
                border:none; border-radius:8px;
            }
            QPushButton:hover   { background:#1DB354; }
            QPushButton:pressed { background:#178A42; }
        """)
        wa_btn.clicked.connect(self._send_renewal)
        lay.addWidget(wa_btn)

        # زر إغلاق
        close_btn = QPushButton("تذكيرني لاحقاً — إغلاق")
        close_btn.setFixedHeight(38)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#888;
                font-size:12px; font-weight:600;
                border:1px solid #CCC; border-radius:7px;
            }
            QPushButton:hover { background:#F5F5F5; color:#555; }
        """)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)

        return w

    # ── المنطق ───────────────────────────────────────────────────────────────

    def _copy_hw(self) -> None:
        hw = self._hw_field.text()
        if hw and hw != "—":
            QApplication.clipboard().setText(hw)
        orig = self._copy_btn.text()
        self._copy_btn.setText("✅ تم النسخ")
        QTimer.singleShot(1800, lambda: self._copy_btn.setText(orig))

    def _send_renewal(self) -> None:
        hw_id     = self._hw_field.text()
        days_str  = f"متبقٍّ {self._days_left} يوم" if self._days_left else "الترخيص منتهٍ"
        expiry    = self._expiry_date or "—"
        msg = (
            f"السلام عليكم،\n\n"
            f"أرغب في تجديد ترخيص نظام ATPAS.\n\n"
            f"معرّف الجهاز (Hardware ID):\n{hw_id}\n\n"
            f"حالة الترخيص: {days_str}\n"
            f"تاريخ الانتهاء: {expiry}\n\n"
            f"يرجى إرسال كود التجديد. شكراً"
        )
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(msg)}")
        self.accept()
