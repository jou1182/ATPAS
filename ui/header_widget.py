#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Branded application header for ATPAS.

Shows: logomark • Arabic product name • version badge (with build date tooltip)
       • animated codes counter • help button (❓).

Fixed height (~72 px). Dark navy background with gold accent.
"""

from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
from ui.motion import prefers_reduced_motion
from ui import theme

# Pre-computed hex constants (sin/cos 30°, 60°) — avoids importing math
_S30 = 0.5       # sin(30°)
_C30 = 0.866     # cos(30°) = √3/2

_VERSION = "3.1"


def _load_build_info() -> dict:
    """قراءة version.json من مجار عمل النظام (CWD)."""
    for candidate in [Path("version.json"), Path(__file__).parent.parent / "version.json"]:
        try:
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


class _AnimatedCounter(QLabel):
    """Counter label that smoothly interpolates to a new integer (exponential ease-out)."""

    def __init__(self, parent=None) -> None:
        super().__init__("", parent)
        self._current: int = 0
        self._target:  int = 0
        self._timer = QTimer(self)
        self._timer.setInterval(16)   # ~60 fps
        self._timer.timeout.connect(self._step)

    def set_count(self, n: int) -> None:
        if prefers_reduced_motion():
            self._target = n
            self._current = n
            self._timer.stop()
            self._refresh()
            return
        if n == self._target:
            return
        self._target = n
        if not self._timer.isActive():
            self._timer.start()

    def _step(self) -> None:
        diff = self._target - self._current
        if diff == 0:
            self._timer.stop()
            return
        delta = max(1, abs(diff) * 35 // 100)
        if diff > 0:
            self._current = min(self._current + delta, self._target)
        else:
            self._current = max(self._current - delta, self._target)
        self._refresh()

    def _refresh(self) -> None:
        n = self._current
        self.setText(f"◉  {n} كود نشط" if n else "")


def _make_hex_path(cx: float, cy: float, r: float) -> QPainterPath:
    path = QPainterPath()
    pts = [
        (cx + r,        cy),
        (cx + r * _S30, cy + r * _C30),
        (cx - r * _S30, cy + r * _C30),
        (cx - r,        cy),
        (cx - r * _S30, cy - r * _C30),
        (cx + r * _S30, cy - r * _C30),
    ]
    path.moveTo(*pts[0])
    for pt in pts[1:]:
        path.lineTo(*pt)
    path.closeSubpath()
    return path


class LogoMark(QWidget):
    """Engineering hexagonal seal — 50×50 px."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(50, 50)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        gold   = QColor("#C9921B")
        gold2  = QColor("#E8C050")
        navy   = QColor("#152433")

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r_out  = min(w, h) / 2.0 - 2.0
        r_in   = r_out * 0.64

        p.setPen(Qt.NoPen)
        p.setBrush(navy)
        p.drawPath(_make_hex_path(cx, cy, r_out))

        pen_ring = QPen(gold, 2.8)
        p.setPen(pen_ring)
        p.setBrush(Qt.NoBrush)
        p.drawPath(_make_hex_path(cx, cy, r_out - 0.5))

        pen_in = QPen(gold, 0.9)
        pen_in.setStyle(Qt.SolidLine)
        p.setPen(pen_in)
        p.drawPath(_make_hex_path(cx, cy, r_in))

        r_a   = r_out * 0.52
        top_y = cy - r_a * 0.80
        bas_y = cy + r_a * 0.80
        bar_y = cy + r_a * 0.08
        hw    = r_a * 0.62
        barhw = r_a * 0.40

        pen_a = QPen(gold2, 3.5)
        pen_a.setCapStyle(Qt.RoundCap)
        pen_a.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen_a)
        p.setBrush(Qt.NoBrush)

        p.drawLine(int(cx), int(top_y), int(cx - hw), int(bas_y))
        p.drawLine(int(cx), int(top_y), int(cx + hw), int(bas_y))
        p.drawLine(int(cx - barhw), int(bar_y), int(cx + barhw), int(bar_y))

        p.setPen(Qt.NoPen)
        p.setBrush(gold2)
        apex_r = 2.2
        p.drawEllipse(
            int(cx - apex_r), int(top_y - apex_r),
            int(apex_r * 2),  int(apex_r * 2),
        )
        p.end()


class HeaderWidget(QWidget):
    """Dark branded header bar with help button and build-date badge."""

    #: يُطلق عند الضغط على زر المساعدة — MainWindow يستمع ويفتح HelpDialog
    help_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر الاستيراد — MainWindow يفتح ImportWizardDialog
    import_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر النسخ الاحتياطي — MainWindow يفتح BackupDialog
    backup_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر الإعدادات — MainWindow يفتح SettingsDialog
    settings_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر صحة النظام — MainWindow يفتح SystemHealthDialog
    health_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر إدارة الأكواد — MainWindow يفتح CodeManagerDialog
    code_manager_requested = pyqtSignal()
    #: يفتح آخر عرض Word تم إنشاؤه
    last_proposal_requested = pyqtSignal()
    #: يعرض بطاقة تعريف النظام
    about_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر استيراد جدول الكميات — MainWindow يفتح BOQReviewPanel
    boq_import_requested = pyqtSignal()

    def __init__(self, active_codes: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(72)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_info = _load_build_info()
        self._setup(active_codes)

    def _setup(self, active_codes: int) -> None:
        self.setStyleSheet("""
            QWidget#appHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1C3045,
                    stop:0.5 #152433,
                    stop:1   #0D1C2B);
                border-bottom: 4px solid #C9921B;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # ── شعار هندسي ─────────────────────────────────────────────────
        logo = LogoMark(self)

        # ── اسم المنتج ─────────────────────────────────────────────────
        name_lbl = QLabel("نظام بناء العروض الفنية", self)
        name_lbl.setStyleSheet(f"""
            color: #FFFFFF; font-size: {theme.TITLE_FONT_SIZE}px; font-weight: 800;
            font-family: {theme.MAIN_FONT};
            background: transparent; letter-spacing: 0.3px;
        """)

        # ── اسم الشركة ─────────────────────────────────────────────────
        brand_lbl = QLabel("الرواف", self)
        brand_lbl.setStyleSheet(f"""
            color: {theme.ACCENT}; font-size: 15px; font-weight: 700;
            background: transparent; padding-right: 6px;
            border-right: 2px solid {theme.ACCENT}50;
        """)

        layout.addWidget(logo)
        layout.addWidget(name_lbl)
        layout.addWidget(brand_lbl)
        layout.addStretch()

        # ── عداد الأكواد المتحرك ────────────────────────────────────────
        self._counter_lbl = _AnimatedCounter(self)
        self._counter_lbl.setStyleSheet(f"""
            color: #C8A860; font-size: {theme.BASE_FONT_SIZE}px; font-weight: 600;
            background: transparent; letter-spacing: 0.4px;
        """)
        self._set_counter(active_codes)
        layout.addWidget(self._counter_lbl)

        # ── شارة الإصدار مع تلميح تاريخ البناء ────────────────────────
        build_date = self._build_info.get("build_date", "dev")
        build_time = self._build_info.get("build_time", "")
        build_label = self._build_info.get("build_label", "")

        if build_date == "dev":
            # وضع تطوير — خلفية حمراء تحذيرية لا يمكن تجاهلها
            ver_lbl = QLabel(f"⚠ DEV v{_VERSION}", self)
            ver_lbl.setToolTip(
                "⚠ وضع التطوير — هذا الكود يعمل مباشرة من Python\n"
                "لبناء EXE جاهز للتوزيع: شغّل build_exe.bat\n"
                "التغييرات الجديدة تظهر فوراً بدون إعادة بناء."
            )
            ver_lbl.setStyleSheet("""
                color: #FFFFFF; background: #C62828;
                font-size: 11px; font-weight: 800;
                padding: 4px 12px; border-radius: 5px; letter-spacing: 0.5px;
                border: 2px solid #FF5252;
            """)
        else:
            ver_lbl = QLabel(f"v{_VERSION}", self)
            ver_lbl.setToolTip(
                f"الإصدار: {_VERSION}\n"
                f"تاريخ البناء: {build_date}\n"
                f"وقت البناء: {build_time}\n"
                f"{build_label}"
            )
            ver_lbl.setStyleSheet("""
                color: #152433; background: #C9921B;
                font-size: 11px; font-weight: 800;
                padding: 4px 12px; border-radius: 5px; letter-spacing: 0.5px;
            """)
        ver_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver_lbl)

        # ── قالب CSS مشترك لأزرار الشريط العلوي ────────────────────────────
        _hdr_btn_style = """
            QPushButton {{
                color: {fg};
                background: transparent;
                border: 1px solid {border};
                border-radius: 5px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {hover_bg};
                border-color: {hover_border};
            }}
            QPushButton:pressed {{
                background: {pressed_bg};
            }}
        """
        # ── زر النسخ الاحتياطي 🗄️ ──────────────────────────────────────────
        backup_btn = QPushButton("🗄️  نسخ احتياطي", self)
        backup_btn.setToolTip("إدارة النسخ الاحتياطية للبيانات (Ctrl+B)")
        backup_btn.setCursor(Qt.PointingHandCursor)
        backup_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#8BC34A",
            border="#8BC34A70",
            hover_bg="#8BC34A20",
            hover_border="#8BC34A",
            pressed_bg="#8BC34A40",
        ))
        backup_btn.clicked.connect(self.backup_requested.emit)
        layout.addWidget(backup_btn)

        # ── زر الاستيراد 📥 ─────────────────────────────────────────────
        import_btn = QPushButton("📥  استيراد", self)
        import_btn.setToolTip("استيراد أكواد جديدة أو إدارة الجهات المالكة (Ctrl+I)")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#5CB8E8",
            border="#5CB8E870",
            hover_bg="#5CB8E820",
            hover_border="#5CB8E8",
            pressed_bg="#5CB8E840",
        ))
        import_btn.clicked.connect(self.import_requested.emit)
        layout.addWidget(import_btn)

        # ── زر استيراد جدول الكميات 📋 ─────────────────────────────────
        boq_btn = QPushButton("📋  جدول كميات", self)
        boq_btn.setToolTip("استورد جدول كميات BOQ وحدد الأكواد المناسبة تلقائياً")
        boq_btn.setCursor(Qt.PointingHandCursor)
        boq_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#FF8A65",
            border="#FF8A6570",
            hover_bg="#FF8A6520",
            hover_border="#FF8A65",
            pressed_bg="#FF8A6540",
        ))
        boq_btn.clicked.connect(self.boq_import_requested.emit)
        layout.addWidget(boq_btn)

        # ── زر صحة النظام 🩺 ───────────────────────────────────────────
        health_btn = QPushButton("🩺  الصحة", self)
        health_btn.setToolTip("فحص الأكواد والجهات وملفات Word")
        health_btn.setCursor(Qt.PointingHandCursor)
        health_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#6EC6A4",
            border="#6EC6A470",
            hover_bg="#6EC6A420",
            hover_border="#6EC6A4",
            pressed_bg="#6EC6A440",
        ))
        health_btn.clicked.connect(self.health_requested.emit)
        layout.addWidget(health_btn)

        # ── زر إدارة الأكواد 🧩 ────────────────────────────────────────
        codes_btn = QPushButton("🧩  الأكواد", self)
        codes_btn.setToolTip("إضافة أو تعديل أو تعطيل الأكواد بدون فتح JSON")
        codes_btn.setCursor(Qt.PointingHandCursor)
        codes_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#E8C050",
            border="#E8C05070",
            hover_bg="#E8C05020",
            hover_border="#E8C050",
            pressed_bg="#E8C05040",
        ))
        codes_btn.clicked.connect(self.code_manager_requested.emit)
        layout.addWidget(codes_btn)

        # ── زر آخر عرض 📄 ─────────────────────────────────────────────
        last_btn = QPushButton("📄  آخر عرض", self)
        last_btn.setToolTip("فتح آخر ملف Word تم إنشاؤه")
        last_btn.setCursor(Qt.PointingHandCursor)
        last_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#F1D68A",
            border="#F1D68A70",
            hover_bg="#F1D68A20",
            hover_border="#F1D68A",
            pressed_bg="#F1D68A40",
        ))
        last_btn.clicked.connect(self.last_proposal_requested.emit)
        layout.addWidget(last_btn)

        # ── زر عن النظام ⓘ ────────────────────────────────────────────
        about_btn = QPushButton("ⓘ  عن النظام", self)
        about_btn.setToolTip("معلومات الإصدار والصحة وآخر نشاط")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#D7DDE8",
            border="#D7DDE870",
            hover_bg="#D7DDE820",
            hover_border="#D7DDE8",
            pressed_bg="#D7DDE840",
        ))
        about_btn.clicked.connect(self.about_requested.emit)
        layout.addWidget(about_btn)

        # ── زر المساعدة ❓ ──────────────────────────────────────────────
        help_btn = QPushButton("❓  مساعدة", self)
        help_btn.setToolTip("فتح دليل المساعدة (F1)")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#C9921B",
            border="#C9921B70",
            hover_bg="#C9921B20",
            hover_border="#C9921B",
            pressed_bg="#C9921B40",
        ))
        help_btn.clicked.connect(self.help_requested.emit)
        layout.addWidget(help_btn)

        # ── زر الإعدادات ⚙ ─────────────────────────────────────────────
        settings_btn = QPushButton("⚙  إعدادات", self)
        settings_btn.setToolTip("إعدادات التشغيل والحفظ")
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setStyleSheet(_hdr_btn_style.format(
            fg="#D7B56D",
            border="#D7B56D70",
            hover_bg="#D7B56D20",
            hover_border="#D7B56D",
            pressed_bg="#D7B56D40",
        ))
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)

    def _set_counter(self, n: int) -> None:
        self._counter_lbl.set_count(n)

    def update_counter(self, n: int) -> None:
        """Smoothly animate the counter to the new code count."""
        self._counter_lbl.set_count(n)
