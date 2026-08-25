#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-009: Preset Scenarios panel.

- Reads presets.json and groups presets by their "group" field.
- Renders one collapsible QGroupBox per group, with one QPushButton per preset.
- Emits preset_applied(list[str], str, list[str]) → (project_ids, owner_id, code_ids).
- Toggle button collapses/expands the entire panel to save vertical space.
"""

from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from ui import theme
from ui.motion import motion_ms, prefers_reduced_motion

# Distinct colours per preset group (border accent only — stays subtle)
_GROUP_COLORS: dict[str, str] = {
    "صرف صحي":        theme.CTX_INFRA,
    "مياه":            theme.CTX_WATER,
    "طرق وأسفلت":     theme.CTX_ROAD,
    "إنشاءات":         theme.CTX_BUILD,
    "مشاريع مزدوجة":   theme.CTX_MIXED,
}
_DEFAULT_COLOR = theme.NEUTRAL

# ارتفاع الشريط المفتوح — مصدر وحيد (يُستخدم في البناء والطي والأنيميشن)
_EXPANDED_H = 125   # px


class PresetsPanelWidget(QWidget):
    """Collapsible strip of grouped preset-apply buttons."""

    # Emitted when user clicks a preset button
    preset_applied   = pyqtSignal(list, str, list)   # project_ids, owner_id, code_ids
    # Emitted when user clicks "Save Preset" — main_window handles the data collection
    save_requested   = pyqtSignal()
    # Emitted when user clicks "History"
    history_requested = pyqtSignal()

    def __init__(self, presets_data: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self._presets: dict[str, dict] = presets_data.get("presets", {})

        # ── outer vertical layout ─────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── header row (always visible) ───────────────────────────────
        header = QFrame()
        header.setLayoutDirection(Qt.RightToLeft)
        header.setFrameShape(QFrame.NoFrame)
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setStyleSheet(f"""
            QFrame {{
                background: {theme.NAVY_SOFT};
                border-radius: 8px 8px 0 0;
                padding: 0;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        title_lbl = QLabel("⚡  الأنماط الجاهزة")
        title_lbl.setStyleSheet(f"color: {theme.ACCENT}; font-weight: 700; font-size: 13px; background: transparent;")
        title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        _btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {theme.NAVY_MUTED};
                border: 1px solid {theme.NAVY_LINE};
                border-radius: 5px;
                font-size: 11px;
                padding: 2px 8px;
            }}
            QPushButton:hover {{ background: {theme.NAVY_LINE}; color: white; }}
        """

        self._toggle_btn = QPushButton("▲ إخفاء")
        self._toggle_btn.setFixedWidth(80)
        self._toggle_btn.setStyleSheet(_btn_style)
        self._toggle_btn.clicked.connect(self._toggle_panel)

        save_btn = QPushButton("💾 حفظ")
        save_btn.setFixedWidth(70)
        save_btn.setToolTip("حفظ الاختيار الحالي كنمط جاهز جديد")
        save_btn.setStyleSheet(_btn_style)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_requested.emit)

        hist_btn = QPushButton("📋 سجل")
        hist_btn.setFixedWidth(70)
        hist_btn.setToolTip("عرض آخر 10 عمليات بناء مع إمكانية إعادة التطبيق")
        hist_btn.setStyleSheet(_btn_style)
        hist_btn.setCursor(Qt.PointingHandCursor)
        hist_btn.clicked.connect(self.history_requested.emit)

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(save_btn)
        header_layout.addWidget(hist_btn)
        header_layout.addWidget(self._toggle_btn)
        outer.addWidget(header)

        # ── content area (collapsible) ────────────────────────────────
        self._content = QWidget()
        self._content.setLayoutDirection(Qt.RightToLeft)
        self._content.setStyleSheet(f"background: {theme.NAVY_DEEP};")
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(8, 6, 8, 6)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignRight)

        self._build_group_boxes(content_layout)

        # Wrap in scroll area (horizontal scroll if many groups)
        scroll = QScrollArea()
        scroll.setWidget(self._content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setFixedHeight(_EXPANDED_H)    # compact strip height (extra room for explicit title label)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {theme.NAVY_DEEP};
                border: none;
                border-radius: 0 0 8px 8px;
            }}
            QScrollArea > QWidget > QWidget {{ background: {theme.NAVY_DEEP}; }}
        """)

        self._scroll_wrapper = scroll
        outer.addWidget(scroll)

        self._expanded = True
        self._toggle_anim: QPropertyAnimation | None = None
        self._active_button_anims: list[QPropertyAnimation] = []

        # الارتفاع يُحسب من محتوى الشريط الفعلي (يتكيف مع DPI وتكبير خطوط
        # Windows) بدل رقم مثبت كان يقصّ عناوين المجموعات على الشاشات المكبرة.
        self._expanded_h = self._measure_expanded_height(scroll)
        scroll.setFixedHeight(self._expanded_h)

    @staticmethod
    def _measure_expanded_height(scroll: QScrollArea, fallback: int = _EXPANDED_H) -> int:
        """ارتفاع الشريط المفتوح = sizeHint للمحتوى + هوامش، بحدود آمنة."""
        content = scroll.widget()
        if content is None:
            return fallback
        hint = content.sizeHint().height()
        hint += content.layout().contentsMargins().top() if content.layout() else 0
        hint += content.layout().contentsMargins().bottom() if content.layout() else 0
        return max(96, min(int(hint) + 8, 260))

    # ------------------------------------------------------------------
    # Build group boxes
    # ------------------------------------------------------------------

    def _build_group_boxes(self, layout: QHBoxLayout) -> None:
        """Group presets by their 'group' field and build one QGroupBox each."""
        groups: dict[str, list[tuple[str, dict]]] = {}
        for pid, pdata in self._presets.items():
            gname = pdata.get("group", "عام")
            groups.setdefault(gname, []).append((pid, pdata))

        # Stable display order — use insertion order from presets.json
        seen_groups: list[str] = []
        for pdata in self._presets.values():
            gname = pdata.get("group", "عام")
            if gname not in seen_groups:
                seen_groups.append(gname)

        for gname in seen_groups:
            presets_in_group = groups.get(gname, [])
            color = _GROUP_COLORS.get(gname, _DEFAULT_COLOR)

            # QGroupBox with NO built-in title — avoids Qt subcontrol clipping bugs.
            # The group name is rendered by an explicit QLabel at the top of the layout.
            box = QGroupBox()
            box.setLayoutDirection(Qt.RightToLeft)
            box.setStyleSheet(
                f"QGroupBox {{"
                f"  border: 1px solid {color}44; border-radius: 8px; "
                f"  margin-top: 0; background: {theme.NAVY_SOFT}; padding: 0;"
                f"}}"
            )
            box_layout = QVBoxLayout(box)
            box_layout.setSpacing(3)
            box_layout.setContentsMargins(7, 6, 7, 5)

            # Explicit title label — guaranteed to render the full group name
            title_lbl = QLabel(gname)
            title_lbl.setLayoutDirection(Qt.RightToLeft)
            title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            title_lbl.setStyleSheet(
                f"color: {color}; font-weight: 700; font-size: 10px; "
                f"background: transparent; border: none; "
                f"padding-bottom: 3px; border-bottom: 1px solid {color}33;"
            )
            box_layout.addWidget(title_lbl)

            for preset_id, pdata in presets_in_group:
                btn = self._make_preset_button(preset_id, pdata, color)
                box_layout.addWidget(btn)

            box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            layout.addWidget(box)

        layout.addStretch()

    def _make_preset_button(self, preset_id: str, pdata: dict, color: str) -> QPushButton:
        icon  = pdata.get("icon", "")
        name  = pdata.get("name_ar", preset_id)
        desc  = pdata.get("description_ar", "")
        codes = pdata.get("codes", [])
        pids  = pdata.get("project_ids", [])
        oid   = pdata.get("owner_id", "")
        n     = len(codes)

        # Icon + name on one line, code count as a small trailing badge
        # Keep Arabic and Latin on separate visual chunks to avoid BiDi reordering
        label = f"{icon} {name}  ({n})" if icon else f"{name}  ({n})"
        btn = QPushButton(label)
        btn.setLayoutDirection(Qt.RightToLeft)
        btn.setToolTip(f"{desc}\n\nعدد الأكواد: {n}\nالمشاريع: {', '.join(pids)}\nالجهة: {oid}")
        btn.setStyleSheet(
            f"QPushButton {{"
            f"  text-align: right; padding: 3px 10px 3px 8px;"
            f"  border: 1px solid {color}55; border-radius: 5px;"
            f"  font-size: 11px; color: {theme.NAVY_TEXT}; background: {theme.NAVY_DEEP};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {color}30; border-color: {color}; color: #FFFFFF;"
            f"}}"
            f"QPushButton:pressed {{ background: {color}50; }}"
        )
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setMinimumWidth(130)   # prevent buttons from squeezing below readable width

        btn.pressed.connect(lambda b=btn: self._press_feedback(b))
        btn.clicked.connect(
            lambda _=None, p=pids, o=oid, c=codes: self.preset_applied.emit(p, o, c)
        )
        return btn

    def _press_feedback(self, btn: QPushButton) -> None:
        """Quick opacity feedback for preset button presses."""
        if prefers_reduced_motion() or not btn.isEnabled():
            return

        effect = QGraphicsOpacityEffect(btn)
        effect.setOpacity(0.78)
        btn.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", btn)
        anim.setDuration(motion_ms(130))
        anim.setStartValue(0.78)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)

        self._active_button_anims.append(anim)

        def _cleanup() -> None:
            btn.setGraphicsEffect(None)
            if anim in self._active_button_anims:
                self._active_button_anims.remove(anim)

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    # ------------------------------------------------------------------
    # Toggle
    # ------------------------------------------------------------------

    def refresh(self, new_presets_data: dict) -> None:
        """Reload panel content after saving a new preset."""
        self._presets = new_presets_data.get("presets", {})
        # Clear old content and rebuild
        old_layout = self._content.layout()
        while old_layout.count():
            item = old_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._build_group_boxes(old_layout)
        # أعد قياس الارتفاع — قد يختلف عدد المجموعات بعد الحفظ
        self._expanded_h = self._measure_expanded_height(self._scroll_wrapper)
        self._scroll_wrapper.setFixedHeight(self._expanded_h)

    def _toggle_panel(self) -> None:
        self._expanded = not self._expanded
        self._toggle_btn.setText("▲ إخفاء" if self._expanded else "▼ عرض")

        _ANIM_MS = 230

        if prefers_reduced_motion():
            self._scroll_wrapper.setVisible(self._expanded)
            self._scroll_wrapper.setMaximumHeight(self._expanded_h if self._expanded else 0)
            return

        if self._expanded:
            # Make visible before animating (height starts at 0)
            self._scroll_wrapper.setVisible(True)
            self._scroll_wrapper.setMaximumHeight(0)

        anim = QPropertyAnimation(self._scroll_wrapper, b"maximumHeight", self)
        anim.setDuration(motion_ms(_ANIM_MS))
        anim.setStartValue(self._scroll_wrapper.maximumHeight())
        anim.setEndValue(self._expanded_h if self._expanded else 0)
        anim.setEasingCurve(
            QEasingCurve.OutCubic if self._expanded else QEasingCurve.InCubic
        )

        if not self._expanded:
            # Hide the widget only *after* the collapse finishes
            anim.finished.connect(lambda: self._scroll_wrapper.setVisible(False))

        self._toggle_anim = anim
        anim.start(QPropertyAnimation.DeleteWhenStopped)
