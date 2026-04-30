#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
شاشة تفعيل الترخيص — تظهر عند أول تشغيل أو عند انتهاء الصلاحية.

الخطوات التي يراها المستخدم:
  1. الشاشة تعرض Hardware ID جهازه
  2. يرسل الـ ID للمطوّر (عبر واتساب / بريد)
  3. يستلم كود الترخيص
  4. يُدخله ويضغط «تفعيل»
  5. البرنامج يفتح
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.license_manager import activate, get_hardware_id


class ActivationDialog(QDialog):
    """نافذة تفعيل الترخيص."""

    def __init__(self, message: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("تفعيل نظام ATPAS — الرواف")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(560)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )

        self._hw_id  = get_hardware_id()
        self._result = False
        self._build_ui(message)

    # ──────────────────────────────────────────────────────────────────────
    # بناء الواجهة
    # ──────────────────────────────────────────────────────────────────────

    def _build_ui(self, status_message: str) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── شريط العنوان الداكن ──────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #1C3045, stop:1 #0D1C2B);
            border-bottom: 3px solid #C9921B;
        """)
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(24, 18, 24, 18)
        h_lay.setSpacing(4)

        title = QLabel("🔐  تفعيل نظام ATPAS")
        title.setStyleSheet(
            "color:#FFFFFF; font-size:18px; font-weight:800; background:transparent;"
        )
        title.setAlignment(Qt.AlignRight)

        sub = QLabel("نظام بناء العروض الفنية — الرواف للمقاولات")
        sub.setStyleSheet(
            "color:#C9921B; font-size:12px; font-weight:600; background:transparent;"
        )
        sub.setAlignment(Qt.AlignRight)

        h_lay.addWidget(title)
        h_lay.addWidget(sub)
        root.addWidget(header)

        # ── منطقة المحتوى ────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background:#F5F0E8;")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(24, 20, 24, 20)
        b_lay.setSpacing(16)

        # رسالة الحالة (تنبيه إذا كان هناك سبب للتفعيل)
        if status_message:
            msg_lbl = QLabel(f"⚠  {status_message}")
            msg_lbl.setWordWrap(True)
            msg_lbl.setStyleSheet("""
                background:#FFF4E5; color:#8B4513; font-size:12px; font-weight:600;
                border:1px solid #F5C066; border-radius:6px; padding:10px 14px;
            """)
            msg_lbl.setAlignment(Qt.AlignRight)
            b_lay.addWidget(msg_lbl)

        # خطوة ① — Hardware ID
        b_lay.addWidget(self._section_label("① معرّف جهازك (أرسله للحصول على الكود)"))

        hw_row = QHBoxLayout()
        self._hw_display = QLineEdit(self._hw_id)
        self._hw_display.setReadOnly(True)
        self._hw_display.setAlignment(Qt.AlignCenter)
        self._hw_display.setStyleSheet("""
            background:#FFFFFF; border:1.5px solid #C9921B;
            border-radius:6px; padding:8px 12px;
            font-family:'Consolas','Courier New',monospace;
            font-size:15px; font-weight:700; color:#152433;
            letter-spacing:2px;
        """)

        copy_btn = QPushButton("📋 نسخ")
        copy_btn.setFixedWidth(80)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet("""
            QPushButton {
                background:#C9921B; color:white; border:none;
                border-radius:6px; padding:8px; font-size:12px; font-weight:700;
            }
            QPushButton:hover  { background:#A77218; }
            QPushButton:pressed{ background:#8A5E14; }
        """)
        copy_btn.clicked.connect(self._copy_hw_id)

        hw_row.addWidget(self._hw_display, stretch=1)
        hw_row.addWidget(copy_btn)
        b_lay.addLayout(hw_row)

        hint = QLabel(
            "أرسل هذا الكود عبر واتساب أو البريد لمشرف النظام للحصول على كود الترخيص."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#5A6B7C; font-size:11px;")
        hint.setAlignment(Qt.AlignRight)
        b_lay.addWidget(hint)

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#D5CFBF;")
        b_lay.addWidget(sep)

        # خطوة ② — إدخال الكود
        b_lay.addWidget(self._section_label("② أدخل كود الترخيص الذي استلمته"))

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("ATPAS-XXXX-XXXXXXXXXXXX")
        self._key_input.setAlignment(Qt.AlignCenter)
        self._key_input.setStyleSheet("""
            background:#FFFFFF; border:1.5px solid #C3BBAA;
            border-radius:6px; padding:10px 14px;
            font-family:'Consolas','Courier New',monospace;
            font-size:14px; letter-spacing:1px; color:#121B28;
        """)
        self._key_input.textChanged.connect(self._on_key_changed)
        self._key_input.returnPressed.connect(self._on_activate)
        b_lay.addWidget(self._key_input)

        # رسالة حالة التحقق
        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setMinimumHeight(32)
        self._status_lbl.setStyleSheet(
            "font-size:12px; font-weight:600; color:transparent;"
        )
        b_lay.addWidget(self._status_lbl)

        # أزرار
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._activate_btn = QPushButton("🔓  تفعيل البرنامج")
        self._activate_btn.setEnabled(False)
        self._activate_btn.setCursor(Qt.PointingHandCursor)
        self._activate_btn.setStyleSheet("""
            QPushButton {
                background:#2B7549; color:white; border:none;
                border-radius:7px; padding:12px 28px;
                font-size:14px; font-weight:800; min-width:180px;
            }
            QPushButton:hover   { background:#236040; }
            QPushButton:pressed { background:#1B4E33; }
            QPushButton:disabled{
                background:#AFBFB8; color:#E2EDE9;
            }
        """)
        self._activate_btn.clicked.connect(self._on_activate)

        exit_btn = QPushButton("✕  إغلاق")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#B03030;
                border:1px solid #B0303060; border-radius:7px;
                padding:12px 20px; font-size:13px; font-weight:700;
            }
            QPushButton:hover  { background:#FEF0F0; border-color:#B03030; }
            QPushButton:pressed{ background:#FDDDDD; }
        """)
        exit_btn.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(exit_btn)
        btn_row.addWidget(self._activate_btn)
        b_lay.addLayout(btn_row)

        root.addWidget(body)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight)
        lbl.setStyleSheet(
            "font-size:12px; font-weight:700; color:#152433;"
            "padding-bottom:2px; border-bottom:1px solid #D5CFBF;"
        )
        return lbl

    # ──────────────────────────────────────────────────────────────────────
    # أحداث
    # ──────────────────────────────────────────────────────────────────────

    def _copy_hw_id(self) -> None:
        """ينسخ Hardware ID إلى الحافظة."""
        QApplication.clipboard().setText(self._hw_id)
        # تأكيد مرئي مؤقت
        btn = self.sender()
        if btn:
            original = btn.text()
            btn.setText("✅ تم النسخ")
            QTimer.singleShot(1500, lambda: btn.setText(original))

    def _on_key_changed(self, text: str) -> None:
        """يُفعّل زر التفعيل بمجرد أن يبدو الكود كاملاً."""
        cleaned = text.strip().upper().replace(" ", "").replace("-", "")
        # ATPAS + 4 + 12 = 20 chars بعد حذف الفواصل
        looks_complete = len(cleaned) >= 16
        self._activate_btn.setEnabled(looks_complete)
        self._clear_status()

    def _on_activate(self) -> None:
        """يتحقق من الكود ويُفعّل البرنامج."""
        key = self._key_input.text().strip()
        if not key:
            return

        self._activate_btn.setEnabled(False)
        self._activate_btn.setText("⏳  جارٍ التحقق...")

        result = activate(key)

        self._activate_btn.setEnabled(True)
        self._activate_btn.setText("🔓  تفعيل البرنامج")

        if result.get("valid") and result.get("activated"):
            self._show_status(result["message"], success=True)
            self._result = True
            QTimer.singleShot(1200, self.accept)
        else:
            self._show_status(result.get("message", "كود غير صحيح"), success=False)
            self._key_input.setStyleSheet(
                self._key_input.styleSheet()
                + "border-color:#B03030; background:#FEF5F5;"
            )

    def _show_status(self, msg: str, *, success: bool) -> None:
        color = "#2B7549" if success else "#B03030"
        bg    = "#EAF5EF" if success else "#FEF0F0"
        self._status_lbl.setText(msg)
        self._status_lbl.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{color};"
            f"background:{bg}; border-radius:5px; padding:6px;"
        )

    def _clear_status(self) -> None:
        self._status_lbl.setText("")
        self._status_lbl.setStyleSheet(
            "font-size:12px; font-weight:600; color:transparent;"
        )
        self._key_input.setStyleSheet("""
            background:#FFFFFF; border:1.5px solid #C3BBAA;
            border-radius:6px; padding:10px 14px;
            font-family:'Consolas','Courier New',monospace;
            font-size:14px; letter-spacing:1px; color:#121B28;
        """)

    # ──────────────────────────────────────────────────────────────────────
    # نتيجة الحوار
    # ──────────────────────────────────────────────────────────────────────

    def was_activated(self) -> bool:
        return self._result
