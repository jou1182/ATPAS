#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Branded application header for ATPAS.

Shows: logomark • Arabic product name • company brand • version badge
(with build date tooltip) • animated codes counter • action buttons.

Fixed height (~72 px). Dark navy background with gold accent.
All colours come from ui.theme (SSOT); all branding comes from
utils.company_profile (white-label SSOT).
"""

from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
from ui.motion import prefers_reduced_motion
from ui import theme
from utils.company_profile import get_company_profile

# Pre-computed hex constants (sin/cos 30°, 60°) — avoids importing math
_S30 = 0.5       # sin(30°)
_C30 = 0.866     # cos(30°) = √3/2


def _load_build_info() -> dict:
    """قراءة version.json من مجار عمل النظام (CWD)."""
    for candidate in [Path("version.json"), Path(__file__).parent.parent / "version.json"]:
        try:
            with open(candidate, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


_VERSION = str(_load_build_info().get("version", "dev"))


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

        gold   = QColor(theme.ACCENT)
        gold2  = QColor("#E8C050")
        navy   = QColor(theme.HEADER)

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


# ── تعريف أزرار الشريط العلوي في جدول واحد ──────────────────────────────────
# (اسم الإشارة، النص، التلميح، لون التمييز)
_HEADER_BUTTONS: list[tuple[str, str, str, str]] = [
    ("backup_requested",           "🗄️  نسخ احتياطي", "إدارة النسخ الاحتياطية للبيانات (Ctrl+B)",              "#8BC34A"),
    ("import_requested",           "📥  استيراد",     "استيراد أكواد جديدة أو إدارة الجهات المالكة (Ctrl+I)",  "#5CB8E8"),
    ("boq_import_requested",       "📋  جدول كميات",  "استورد جدول كميات BOQ وحدد الأكواد المناسبة تلقائياً",   "#FF8A65"),
    ("health_requested",           "🩺  الصحة",       "فحص الأكواد والجهات وملفات Word",                       "#6EC6A4"),
    ("code_manager_requested",     "🧩  الأكواد",     "إضافة أو تعديل أو تعطيل الأكواد بدون فتح JSON",         "#E8C050"),
    ("content_library_requested",  "📚  المكتبة",     "إدارة ملفات Word وحالات اعتماد المحتوى",                "#CFA7FF"),
    ("last_proposal_requested",    "📄  آخر عرض",     "فتح آخر ملف Word تم إنشاؤه",                            "#F1D68A"),
    ("session_history_requested",  "🕐  الجلسات",     "عرض واسترجاع الجلسات المحفوظة (Ctrl+J)",                "#7EC8E3"),
    ("dark_mode_toggle_requested", "🌙  داكن",        "تبديل الوضع الداكن/الفاتح (Ctrl+D)",                    "#9B6BB7"),
    ("about_requested",            "ⓘ  عن النظام",    "معلومات الإصدار والصحة وآخر نشاط",                      "#D7DDE8"),
    ("help_requested",             "❓  مساعدة",      "فتح دليل المساعدة (F1)",                                "#C9921B"),
    ("settings_requested",         "⚙  إعدادات",      "إعدادات التشغيل والحفظ",                                "#D7B56D"),
]

_HDR_BTN_TEMPLATE = """
    QPushButton {{
        color: {fg};
        background: transparent;
        border: 1px solid {border};
        border-radius: 5px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        min-width: 70px;
    }}
    QPushButton:hover {{
        background: {hover_bg};
        border-color: {hover_border};
    }}
    QPushButton:pressed {{
        background: {pressed_bg};
    }}
"""


class HeaderWidget(QWidget):
    """Dark branded header bar with action buttons and build-date badge."""

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
    #: يفتح مركز إدارة مكتبة Word
    content_library_requested = pyqtSignal()
    #: يفتح آخر عرض Word تم إنشاؤه
    last_proposal_requested = pyqtSignal()
    #: يعرض بطاقة تعريف النظام
    about_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر استيراد جدول الكميات — MainWindow يفتح BOQReviewPanel
    boq_import_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر الجلسات المحفوظة — MainWindow يفتح SessionHistoryDialog
    session_history_requested = pyqtSignal()
    #: يُطلق عند الضغط على زر Dark Mode — MainWindow يبدّل الوضع
    dark_mode_toggle_requested = pyqtSignal()

    def __init__(self, active_codes: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("appHeader")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumHeight(60)   # مرن — لا يُقطع على شاشات DPI عالية
        self.setMaximumHeight(90)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_info = _load_build_info()
        self._setup(active_codes)

    # ------------------------------------------------------------------
    # Setup — split into small factories
    # ------------------------------------------------------------------

    def _setup(self, active_codes: int) -> None:
        self.setStyleSheet(f"""
            QWidget#appHeader {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.NAVY_MID},
                    stop:0.5 {theme.HEADER},
                    stop:1   {theme.HEADER2});
                border-bottom: 4px solid {theme.ACCENT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)

        self._add_brand_widgets(layout)
        layout.addStretch()
        self._add_counter_and_badge(layout, active_codes)
        self._add_action_buttons(layout)

    def _add_brand_widgets(self, layout: QHBoxLayout) -> None:
        """الشعار + اسم المنتج + اسم الشركة (من company_profile)."""
        profile = get_company_profile()

        logo = LogoMark(self)
        layout.addWidget(logo)

        name_lbl = QLabel(profile["product_name_ar"], self)
        name_lbl.setStyleSheet(f"""
            color: #FFFFFF; font-size: {theme.TITLE_FONT_SIZE}px; font-weight: 800;
            font-family: {theme.MAIN_FONT};
            background: transparent; letter-spacing: 0.3px;
        """)
        layout.addWidget(name_lbl)

        brand_lbl = QLabel(profile["company_name_ar"], self)
        brand_lbl.setStyleSheet(f"""
            color: {theme.ACCENT}; font-size: 15px; font-weight: 700;
            background: transparent; padding-right: 6px;
            border-right: 2px solid {theme.ACCENT}50;
        """)
        layout.addWidget(brand_lbl)

    def _add_counter_and_badge(self, layout: QHBoxLayout, active_codes: int) -> None:
        """عداد الأكواد المتحرك + شارة الإصدار مع تلميح تاريخ البناء."""
        self._counter_lbl = _AnimatedCounter(self)
        self._counter_lbl.setStyleSheet(f"""
            color: #C8A860; font-size: {theme.BASE_FONT_SIZE}px; font-weight: 600;
            background: transparent; letter-spacing: 0.4px;
        """)
        self._set_counter(active_codes)
        layout.addWidget(self._counter_lbl)

        layout.addWidget(self._build_version_badge())

    def _build_version_badge(self) -> QLabel:
        build_date = self._build_info.get("build_date", "dev")
        build_time = self._build_info.get("build_time", "")
        build_label = self._build_info.get("build_label", "")

        if build_date == "dev":
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
            ver_lbl.setStyleSheet(f"""
                color: {theme.HEADER}; background: {theme.ACCENT};
                font-size: 11px; font-weight: 800;
                padding: 4px 12px; border-radius: 5px; letter-spacing: 0.5px;
            """)
        ver_lbl.setAlignment(Qt.AlignCenter)
        return ver_lbl

    def _make_header_button(self, label: str, tooltip: str, accent: str) -> QPushButton:
        """مصنع زر الشريط العلوي — نمط موحد بلون تمييز لكل زر."""
        btn = QPushButton(label, self)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(_HDR_BTN_TEMPLATE.format(
            fg=accent,
            border=f"{accent}70",
            hover_bg=f"{accent}20",
            hover_border=accent,
            pressed_bg=f"{accent}40",
        ))
        return btn

    def _add_action_buttons(self, layout: QHBoxLayout) -> None:
        """يبني كل أزرار الشريط من الجدول المركزي ويصل الإشارات."""
        for signal_name, label, tooltip, accent in _HEADER_BUTTONS:
            btn = self._make_header_button(label, tooltip, accent)
            # اتصال إشارة-بإشارة: وسيطة checked الزائدة تُهمَل تلقائياً
            btn.clicked.connect(getattr(self, signal_name))
            layout.addWidget(btn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _set_counter(self, n: int) -> None:
        self._counter_lbl.set_count(n)

    def update_counter(self, n: int) -> None:
        """Smoothly animate the counter to the new code count."""
        self._counter_lbl.set_count(n)
