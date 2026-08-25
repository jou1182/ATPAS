#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مكونات واجهة مشتركة — المصدر الوحيد للأنماط المتكررة.

يحتوي على البطاقات وعناوين الأقسام وأوصاف الأزرار التي كانت مُعاد
بناءها يدوياً في أكثر من ثمانية حوارات بألوان صلبة مخالفة لـ SSOT.
أي تعديل مستقبلي على الهوية البصرية يبدأ من هنا ومن ui/theme.py فقط.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from ui import theme


class SectionTitleLabel(QLabel):
    """عنوان قسم: كحلي داكن مع خط ذهبي سفلي — النمط المتكرر في كل الحوارات."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setStyleSheet(f"""
            font-size: 15px; font-weight: 800; color: {theme.HEADER};
            padding-bottom: 6px; border-bottom: 2px solid {theme.ACCENT};
            background: transparent;
        """)


class MetricCard(QFrame):
    """بطاقة مؤشر: قيمة كبيرة + تسمية + شريط علوي بلون دلالي.

    النمط نفسه المستخدم في صحة النظام والمراجعة النهائية وتقرير البناء.
    """

    def __init__(
        self,
        value: str,
        label: str,
        accent: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background: {theme.SURFACE};
                border: 1px solid {theme.BORDER2};
                border-top: 3px solid {accent};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self._value_lbl = QLabel(value)
        self._value_lbl.setAlignment(Qt.AlignCenter)
        self._value_lbl.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {accent};"
            "background: transparent; border: none;"
        )
        layout.addWidget(self._value_lbl)

        self._label_lbl = QLabel(label)
        self._label_lbl.setAlignment(Qt.AlignCenter)
        self._label_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {theme.TEXT2};"
            "background: transparent; border: none;"
        )
        layout.addWidget(self._label_lbl)

    def set_value(self, value: str) -> None:
        """حدّث القيمة المعروضة."""
        self._value_lbl.setText(value)

    def set_label(self, label: str) -> None:
        """حدّث التسمية المعروضة."""
        self._label_lbl.setText(label)


def make_metric_card(
    value: str, label: str, accent: str, parent: QWidget | None = None
) -> MetricCard:
    """اختصار لإنشاء بطاقة مؤشر."""
    return MetricCard(value, label, accent, parent)


def status_banner_css(bg_pale: str, fg: str, border: str | None = None) -> str:
    """نمط شريط الحالة/الجاهزية الموحد (نجاح، تحذير، خطأ، معلومة)."""
    border = border or bg_pale
    return (
        f"background: {bg_pale}; color: {fg};"
        f"border: 1px solid {border}; border-radius: 7px;"
        "padding: 8px 12px; font-weight: 700;"
    )
