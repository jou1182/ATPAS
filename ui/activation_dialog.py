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

from ui import theme
from ui.theme import BORDER, ERROR, ERROR_PALE, SUCCESS, SUCCESS_PALE, TEXT
from utils.license_manager import activate, get_hardware_id, start_trial


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
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {theme.NAVY_MID}, stop:1 {theme.HEADER2});
            border-bottom: 3px solid {theme.ACCENT};
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
            f"color:{theme.ACCENT}; font-size:12px; font-weight:600; background:transparent;"
        )
        sub.setAlignment(Qt.AlignRight)

        h_lay.addWidget(title)
        h_lay.addWidget(sub)
        root.addWidget(header)

        # ── منطقة المحتوى ────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"background:{theme.PARCHMENT_2};")
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
        self._hw_display.setStyleSheet(f"""
            background:#FFFFFF; border:1.5px solid {theme.ACCENT};
            border-radius:6px; padding:8px 12px;
            font-family:'Tajawal';
            font-size:15px; font-weight:700; color:{theme.HEADER};
            letter-spacing:2px;
        """)

        copy_btn = QPushButton("📋 نسخ")
        copy_btn.setFixedWidth(80)
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background:{theme.ACCENT}; color:{theme.HEADER}; border:none;
                border-radius:6px; padding:8px; font-size:12px; font-weight:700;
            }}
            QPushButton:hover  {{ background:{theme.ACCENT_DARK}; color:white; }}
            QPushButton:pressed{{ background:{theme.HEADER2}; color:white; }}
        """)
        copy_btn.clicked.connect(self._copy_hw_id)

        hw_row.addWidget(self._hw_display, stretch=1)
        hw_row.addWidget(copy_btn)
        b_lay.addLayout(hw_row)

        hint = QLabel(
            "أرسل هذا الكود عبر واتساب أو البريد لمشرف النظام للحصول على كود الترخيص."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{theme.TEXT2}; font-size:11px;")
        hint.setAlignment(Qt.AlignRight)
        b_lay.addWidget(hint)

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{theme.BORDER};")
        b_lay.addWidget(sep)

        # خطوة ② — إدخال الكود
        b_lay.addWidget(self._section_label("② أدخل كود الترخيص الذي استلمته"))

        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("ATPAS-XXXX-XXXXXXXXXXXX")
        self._key_input.setAlignment(Qt.AlignCenter)
        self._key_input.setStyleSheet(f"""
            background:#FFFFFF; border:1.5px solid {theme.BORDER2};
            border-radius:6px; padding:10px 14px;
            font-family:'Tajawal';
            font-size:14px; letter-spacing:1px; color:{theme.TEXT};
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
        self._activate_btn.setStyleSheet(f"""
            QPushButton {{
                background:{SUCCESS}; color:white; border:none;
                border-radius:7px; padding:12px 28px;
                font-size:14px; font-weight:800; min-width:180px;
            }}
            QPushButton:hover   {{ background:#236040; }}
            QPushButton:pressed {{ background:#1B4E33; }}
            QPushButton:disabled{{
                background:#AFBFB8; color:#E2EDE9;
            }}
        """)
        self._activate_btn.clicked.connect(self._on_activate)

        exit_btn = QPushButton("✕  إغلاق")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; color:{ERROR};
                border:1px solid {ERROR}60; border-radius:7px;
                padding:12px 20px; font-size:13px; font-weight:700;
            }}
            QPushButton:hover  {{ background:{ERROR_PALE}; border-color:{ERROR}; }}
            QPushButton:pressed{{ background:#FDDDDD; }}
        """)
        exit_btn.clicked.connect(self.reject)

        # ── زر التجربة 🧪 ───────────────────────────────────────────────
        trial_btn = QPushButton("🧪  تجربة البرنامج ليوم واحد")
        trial_btn.setCursor(Qt.PointingHandCursor)
        trial_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; color:#2A6F6A;
                border:2px solid #2A6F6A; border-radius:7px;
                padding:12px 20px; font-size:13px; font-weight:800;
            }}
            QPushButton:hover  {{ background:#E8F5E9; }}
            QPushButton:pressed{{ background:#C8E6C9; }}
        """)
        trial_btn.clicked.connect(self._on_start_trial)

        btn_row.addStretch()
        btn_row.addWidget(exit_btn)
        btn_row.addWidget(trial_btn)
        btn_row.addWidget(self._activate_btn)
        b_lay.addLayout(btn_row)

        root.addWidget(body)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight)
        lbl.setStyleSheet(
            f"font-size:12px; font-weight:700; color:{theme.HEADER};"
            f"padding-bottom:2px; border-bottom:1px solid {theme.BORDER};"
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

    def _on_start_trial(self) -> None:
        """بدء تجربة البرنامج ليوم واحد."""
        result = start_trial()
        if result.get("valid"):
            self._show_status(result["message"], success=True)
            self._result = True
            QTimer.singleShot(1200, self.accept)
        else:
            self._show_status(result.get("message", "تعذّر بدء التجربة"), success=False)

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
                + f"border-color:{ERROR}; background:{ERROR_PALE};"
            )

    def _show_status(self, msg: str, *, success: bool) -> None:
        color = SUCCESS if success else ERROR
        bg    = SUCCESS_PALE if success else ERROR_PALE
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
        self._key_input.setStyleSheet(f"""
            background:#FFFFFF; border:1.5px solid {theme.BORDER2};
            border-radius:6px; padding:10px 14px;
            font-family:'Tajawal';
            font-size:14px; letter-spacing:1px; color:{theme.TEXT};
        """)

    # ──────────────────────────────────────────────────────────────────────
    # نتيجة الحوار
    # ──────────────────────────────────────────────────────────────────────

    def was_activated(self) -> bool:
        return self._result
