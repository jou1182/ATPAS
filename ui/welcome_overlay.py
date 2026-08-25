#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
شاشة الترحيب بالمستخدم الجديد (First-Run Welcome).

تظهر مرة واحدة فقط عند أول تشغيل للتطبيق.
يتم تخزين حالة "تمت مشاهدتها" في ملف صغير بجوار EXE.

الاستدعاء من MainWindow:
    WelcomeOverlay.show_if_first_run(parent=self)
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.motion import motion_ms, prefers_reduced_motion
from ui import theme


def _get_marker_path() -> Path:
    """مسار ملف علامة "شاهدت الترحيب" — بجوار EXE أو في مجلد المشروع."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / ".atpas_welcomed"
    return Path(".atpas_welcomed")


def _is_first_run() -> bool:
    return not _get_marker_path().exists()


def _mark_welcomed() -> None:
    try:
        _get_marker_path().touch()
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# بطاقة خطوة واحدة
# ─────────────────────────────────────────────────────────────────────────────

_STEPS = [
    {
        "num": "1",
        "icon": "🏗️",
        "title": "اختر المشروع والجهة",
        "body": (
            "من أعلى الشاشة، حدد نوع المشروع\n"
            "(صرف صحي، مياه، طرق...) والجهة المالكة.\n"
            "ستظهر الأكواد المناسبة تلقائياً."
        ),
        "bg": "#EEF5FB",
        "border": theme.NAVY_MID,
        "num_fg": "#FDF7E8",
    },
    {
        "num": "2",
        "icon": "☑️",
        "title": "اختر الأكواد",
        "body": (
            "ضع علامة ✓ على كل بند تريده في العرض.\n"
            "استخدم الأنماط الجاهزة لاختيار\n"
            "مجموعات كاملة دفعة واحدة."
        ),
        "bg": "#F3F8EE",
        "border": "#2E7D32",
        "num_fg": "#FFFFFF",
    },
    {
        "num": "3",
        "icon": "📄",
        "title": "ابنِ العرض الفني",
        "body": (
            "راجع المعاينة في اليمين، ثم اضغط\n"
            "«بناء العرض الفني».\n"
            "ملف Word جاهز خلال ثوانٍ!"
        ),
        "bg": "#FFF8E7",
        "border": theme.ACCENT,
        "num_fg": theme.HEADER,
    },
]


def _make_step_card(step: dict, parent: QWidget) -> QWidget:
    card = QWidget(parent)
    card.setStyleSheet(f"""
        QWidget {{
            background: {step['bg']};
            border-right: 5px solid {step['border']};
            border-radius: 10px;
        }}
    """)

    layout = QHBoxLayout(card)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(12)

    # رقم الخطوة
    num_lbl = QLabel(step["num"], card)
    num_lbl.setFixedSize(36, 36)
    num_lbl.setAlignment(Qt.AlignCenter)
    num_lbl.setStyleSheet(f"""
        background: {step['border']}; color: {step.get('num_fg', '#FFFFFF')};
        border-radius: 18px; font-size: 16px; font-weight: 900;
    """)

    # أيقونة
    icon_lbl = QLabel(step["icon"], card)
    icon_lbl.setStyleSheet("font-size: 28px; background: transparent; border: none;")
    icon_lbl.setAlignment(Qt.AlignCenter)

    # نص
    text_col = QVBoxLayout()
    text_col.setSpacing(2)

    title_lbl = QLabel(step["title"], card)
    title_lbl.setStyleSheet(f"""
        font-size: 14px; font-weight: 800; color: {step['border']};
        background: transparent; border: none;
    """)

    body_lbl = QLabel(step["body"], card)
    body_lbl.setStyleSheet(
        "font-size: 11px; color: #333; background: transparent; border: none;"
    )
    body_lbl.setWordWrap(True)

    text_col.addWidget(title_lbl)
    text_col.addWidget(body_lbl)

    layout.addWidget(num_lbl)
    layout.addWidget(icon_lbl)
    layout.addLayout(text_col, stretch=1)

    return card


# ─────────────────────────────────────────────────────────────────────────────
# WelcomeDialog
# ─────────────────────────────────────────────────────────────────────────────

class WelcomeDialog(QDialog):
    """نافذة ترحيب بسيطة تُظهر 3 خطوات للمبتدئين."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("مرحباً بك في نظام ATPAS")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 16)

        # ── عنوان ──────────────────────────────────────────────────────
        header_row = QHBoxLayout()

        logo_lbl = QLabel("🏛️", self)
        logo_lbl.setStyleSheet("font-size: 32px; background: transparent;")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        welcome_lbl = QLabel("مرحباً بك في نظام الرواف", self)
        welcome_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: 900; color: {theme.HEADER};"
        )

        sub_lbl = QLabel("نظام بناء العروض الفنية الهندسية الذكي", self)
        sub_lbl.setStyleSheet("font-size: 12px; color: #666;")

        title_col.addWidget(welcome_lbl)
        title_col.addWidget(sub_lbl)

        header_row.addWidget(logo_lbl)
        header_row.addLayout(title_col, stretch=1)
        layout.addLayout(header_row)

        # ── فاصل ───────────────────────────────────────────────────────
        sep = QWidget(self)
        sep.setFixedHeight(2)
        sep.setStyleSheet(f"background: {theme.ACCENT}; border-radius: 1px;")
        layout.addWidget(sep)

        # ── عنوان البداية ──────────────────────────────────────────────
        guide_lbl = QLabel("⚡ البدء في 3 خطوات بسيطة:", self)
        guide_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {theme.NAVY_MID};"
        )
        layout.addWidget(guide_lbl)

        # ── بطاقات الخطوات ─────────────────────────────────────────────
        self._cards: list[QWidget] = []
        for step in _STEPS:
            card = _make_step_card(step, self)
            layout.addWidget(card)
            self._cards.append(card)

        # ── نصيحة المساعدة ──────────────────────────────────────────────
        tip_lbl = QLabel(
            "💡 في أي وقت اضغط <b>F1</b> أو زر <b>❓ مساعدة</b> في أعلى الشاشة "
            "للعودة لهذا الدليل.",
            self,
        )
        tip_lbl.setStyleSheet(
            f"font-size: 11px; color: #555; background: #FFF8E7; "
            f"border-right: 3px solid {theme.ACCENT}; border-radius: 5px; "
            "padding: 8px 10px;"
        )
        tip_lbl.setWordWrap(True)
        layout.addWidget(tip_lbl)

        # ── أزرار ──────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        dont_show_btn = QPushButton("لا تظهر مجدداً", self)
        dont_show_btn.setStyleSheet("""
            QPushButton {
                color: #888; background: transparent;
                border: 1px solid #CCC; border-radius: 5px;
                padding: 7px 18px; font-size: 11px;
            }
            QPushButton:hover { background: #F5F5F5; }
        """)
        dont_show_btn.clicked.connect(self._dismiss_permanently)

        start_btn = QPushButton("🚀  فهمت، لنبدأ!", self)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme.HEADER}; color: {theme.ACCENT};
                border: none; border-radius: 6px;
                padding: 8px 28px; font-size: 13px; font-weight: 800;
            }}
            QPushButton:hover {{ background: {theme.NAVY_MID}; }}
            QPushButton:pressed {{ background: {theme.HEADER2}; }}
        """)
        start_btn.setDefault(True)
        start_btn.clicked.connect(self.accept)

        btn_row.addWidget(dont_show_btn)
        btn_row.addStretch()
        btn_row.addWidget(start_btn)
        layout.addLayout(btn_row)

        # ── أنيميشن دخول البطاقات (staggered) ─────────────────────────
        if not prefers_reduced_motion():
            self._play_entry_animation()

    def _play_entry_animation(self) -> None:
        """تأثير دخول متتابع للبطاقات الثلاث."""
        for i, card in enumerate(self._cards):
            effect = QGraphicsOpacityEffect(card)
            effect.setOpacity(0.0)
            card.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", card)
            anim.setDuration(motion_ms(360))
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)

            def _cleanup(w=card, a=anim):
                w.setGraphicsEffect(None)

            anim.finished.connect(_cleanup)
            QTimer.singleShot(120 * (i + 1), lambda a=anim: a.start())

    def _dismiss_permanently(self) -> None:
        _mark_welcomed()
        self.accept()

    def accept(self) -> None:
        _mark_welcomed()
        super().accept()


# ─────────────────────────────────────────────────────────────────────────────
# نقطة الدخول العامة
# ─────────────────────────────────────────────────────────────────────────────

def show_if_first_run(parent=None) -> None:
    """أظهر شاشة الترحيب إذا كان هذا أول تشغيل. آمن للاستدعاء دائماً."""
    if _is_first_run():
        WelcomeDialog(parent).exec_()


# ─────────────────────────────────────────────────────────────────────────────
# اختبار مستقل
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # نمحو الملف مؤقتاً للاختبار
    m = _get_marker_path()
    if m.exists():
        m.unlink()
    show_if_first_run()
    sys.exit(0)
