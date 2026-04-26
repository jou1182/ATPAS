#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-003 (v3): Code item selector with proper BiDi typography.

- _CodeItem: custom row widget with three visually-separated zones:
    [✓]  [Arabic name — stretches]  [N صفحة]  [001-SOI-INV]
  Eliminates mixed-direction text rendering by isolating the Latin code
  ID in its own LTR-forced label, away from the Arabic name.
- Filters codes by project_ids (multi) AND owner_id.
- Groups codes into QGroupBox per category (001→005).
- Search box filters codes live by code_id or Arabic name.
- "اختيار الكل" / "إلغاء الكل" per category header.
- Mandatory codes: pre-checked, locked (disabled tick).
- Exclusive group codes (excavation_type): orange warning.
- "إضافة كود مخصص" button: adds a temporary code to the session.
- Emits codes_changed(list[str]) on any state change.
- Shows live counter "X أكواد / Y صفحة".
"""

from __future__ import annotations

import re
from typing import Any

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from ui.motion import motion_single_shot, prefers_reduced_motion

_PROJECT_NAMES: dict[str, str] = {
    "wastewater":           "صرف صحي",
    "water_supply":         "مياه شرب",
    "asphalt":              "أسفلت",
    "road_maintenance":     "صيانة طرق",
    "general_construction": "إنشاءات عامة",
    "water_transmission":   "ناقل مياه",
}
_OWNER_NAMES: dict[str, str] = {
    "nwc":           "NWC",
    "makkah":        "أمانة مكة",
    "moh":           "وزارة الصحة",
    "mot":           "وزارة النقل",
    "nhi":           "NHI",
    "amana_riyadh":  "أمانة الرياض",
    "amana_qassim":  "أمانة القصيم",
    "swa":           "SWA",
    "ksia":          "KSIA",
}

_CATEGORY_NAMES: dict[str, str] = {
    "001": "الأعمال التحضيرية",
    "002": "الحفر والمخلفات",
    "003": "التركيب والتوصيل",
    "004": "الاختبارات والفحوصات",
    "005": "الإنهاء والتسليم",
}
_CATEGORY_COLORS: dict[str, str] = {
    "001": "#1F4F7D",  # preparatory: planning/info
    "002": "#A45D1C",  # excavation: caution/earth
    "003": "#2A6A4B",  # installation: active/constructive
    "004": "#3B5C8C",  # tests: technical/verification
    "005": "#6D5631",  # handover: closure/delivery
}
_CATEGORY_BG: dict[str, str] = {
    "001": "#EEF3FA",
    "002": "#FBF1E8",
    "003": "#EEF6F1",
    "004": "#EEF1F8",
    "005": "#F6F1E8",
}

# Legacy QCheckBox-style CSS strings (preserved for API compatibility)
_MANDATORY_STYLE = "QCheckBox { color: #1565C0; font-weight: bold; }"
_EXCLUSIVE_STYLE = "QCheckBox { color: #E65100; }"
_CUSTOM_STYLE    = "QCheckBox { color: #6A1B9A; font-style: italic; }"

# Regex helpers — parse legacy CSS into label style properties
_COLOR_RE  = re.compile(r'color\s*:\s*(#[0-9A-Fa-f]{3,8})', re.IGNORECASE)
_BOLD_RE   = re.compile(r'font-weight\s*:\s*bold',           re.IGNORECASE)
_ITALIC_RE = re.compile(r'font-style\s*:\s*italic',          re.IGNORECASE)

# Visual tokens (synced with theme.py palette)
_NAME_DEFAULT  = "font-family: Tajawal, 'Segoe UI'; font-size: 12px; color: #1A2433; font-weight: normal; font-style: normal;"
_ID_STYLE      = (
    "font-family: Consolas, 'Courier New', monospace; "
    "font-size: 10px; color: #9BA8B5; letter-spacing: 0.4px;"
)
_BADGE_STYLE   = (
    "font-size: 10px; color: #6B7A8D; background: #EEE9E0; "
    "border-radius: 8px; padding: 1px 6px; margin: 0 2px;"
)
_CAT_HDR_STYLE = "font-size: 11px; font-weight: bold; color: #1B2D40;"


# ---------------------------------------------------------------------------
# Small safe parsing helpers (defensive against malformed JSON values)
# ---------------------------------------------------------------------------

def _safe_int(value: Any, default: int = 0) -> int:
    """Parse int safely; fallback to default on invalid values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# _CodeItem — typography-correct row replacing QCheckBox
# ---------------------------------------------------------------------------

class _CodeItem(QWidget):
    """
    A row widget combining a checkbox indicator with three visual zones:

        RTL layout (right → left):
        [✓] | Arabic name (stretches, 12 px primary)  | N صفحة | 001-SOI-INV
             |                                         | badge  | monospace LTR

    Exposes a QCheckBox-compatible interface (isChecked, setChecked,
    isEnabled, setEnabled, blockSignals, stateChanged, setStyleSheet,
    setVisible, setToolTip) so all callers need no change beyond type hints.
    """

    stateChanged = pyqtSignal(int)   # mirrors QCheckBox.stateChanged(int)

    def __init__(self, code_id: str, name_ar: str, pages: int, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)

        # ── Checkbox tick (no text — label is handled separately) ───────
        self._cb = QCheckBox()
        self._cb.setLayoutDirection(Qt.RightToLeft)
        self._cb.setStyleSheet("spacing: 0; padding: 0;")   # no text → no gap
        self._cb.stateChanged.connect(self.stateChanged.emit)
        self._cb.stateChanged.connect(self._flash_row)

        # ── Arabic name: primary zone, right-aligned, stretches ─────────
        self._name_lbl = QLabel(name_ar)
        self._name_lbl.setLayoutDirection(Qt.RightToLeft)
        # Use absolute right alignment to avoid any style/theme-dependent flips.
        self._name_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter | Qt.AlignAbsolute)
        self._name_lbl.setStyleSheet(_NAME_DEFAULT)

        # ── Pages badge: pill, fixed width ──────────────────────────────
        self._badge_lbl = QLabel(f"{pages} صفحة")
        self._badge_lbl.setAlignment(Qt.AlignCenter)
        self._badge_lbl.setFixedWidth(82)
        self._badge_lbl.setStyleSheet(_BADGE_STYLE)

        # ── Code ID: isolated LTR zone — no BiDi mixing ─────────────────
        self._id_lbl = QLabel(code_id)
        self._id_lbl.setLayoutDirection(Qt.LeftToRight)   # force LTR
        self._id_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._id_lbl.setFixedWidth(124)
        self._id_lbl.setStyleSheet(_ID_STYLE)

        # ── Layout: RTL → first widget is rightmost visually ────────────
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 1, 4, 1)
        lay.setSpacing(6)
        lay.addWidget(self._cb)           # ① right: checkbox tick
        lay.addWidget(self._name_lbl, 1, Qt.AlignRight | Qt.AlignVCenter)  # ② Arabic name
        lay.addWidget(self._badge_lbl)    # ③ pages pill
        lay.addWidget(self._id_lbl)       # ④ left: code ID monospace

        # ── Safe timer for flash feedback (child of self ensures cleanup) ──
        self._flash_timer = QTimer(self)
        self._flash_timer.setSingleShot(True)
        self._flash_timer.timeout.connect(self._clear_flash)

    # ------------------------------------------------------------------
    # Interaction feedback
    # ------------------------------------------------------------------

    def _flash_row(self, state: int) -> None:
        """Brief background highlight to confirm check/uncheck.

        Gold-pale on check, neutral-warm on uncheck — confirms the action
        without distracting from the reading flow.
        """
        if prefers_reduced_motion():
            self._clear_flash()
            return

        pal = QPalette()
        pal.setColor(
            QPalette.Window,
            QColor("#FAF0DC") if state else QColor("#F0EDE6"),
        )
        self.setAutoFillBackground(True)
        self.setPalette(pal)
        self._flash_timer.start(motion_ms(200))

    def _clear_flash(self) -> None:
        """Restore transparent background after the flash completes."""
        self.setAutoFillBackground(False)

    # ------------------------------------------------------------------
    # QCheckBox-compatible interface
    # ------------------------------------------------------------------

    def isChecked(self) -> bool:
        return self._cb.isChecked()

    def setChecked(self, v: bool) -> None:
        self._cb.setChecked(v)

    def isEnabled(self) -> bool:
        return self._cb.isEnabled()

    def setEnabled(self, v: bool) -> None:
        """Enable/disable the checkbox tick. Labels keep their styled color."""
        self._cb.setEnabled(v)
        # Dim secondary labels when locked; name label keeps its styled color
        self._badge_lbl.setEnabled(v)
        self._id_lbl.setEnabled(v)

    def setStyleSheet(self, css: str) -> None:
        """Parse legacy QCheckBox CSS and apply color/weight/style to name label."""
        if not css:
            self._name_lbl.setStyleSheet(_NAME_DEFAULT)
            return
        color_m = _COLOR_RE.search(css)
        color   = color_m.group(1) if color_m else "#1A2433"
        weight  = "bold"   if _BOLD_RE.search(css)   else "normal"
        fstyle  = "italic" if _ITALIC_RE.search(css) else "normal"
        self._name_lbl.setStyleSheet(
            f"font-size: 12px; color: {color}; "
            f"font-weight: {weight}; font-style: {fstyle};"
        )

    def setToolTip(self, tip: str) -> None:  # type: ignore[override]
        super().setToolTip(tip)
        self._cb.setToolTip(tip)
        self._name_lbl.setToolTip(tip)


# ---------------------------------------------------------------------------
# CheckboxSelectorWidget
# ---------------------------------------------------------------------------

class CheckboxSelectorWidget(QGroupBox):
    """Scrollable, grouped code-item list for code selection."""

    codes_changed = pyqtSignal(list)

    def __init__(self, registry_data: dict[str, Any], parent=None) -> None:
        super().__init__("", parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self._all_codes: dict[str, dict] = registry_data.get("codes", {})
        self._checkboxes: dict[str, _CodeItem] = {}
        self._mandatory_codes: set[str] = set()
        self._pending_search: str = ""

        self._counter_label = QLabel("0 أكواد / 0 صفحة")
        self._counter_label.setAlignment(Qt.AlignCenter)

        # Search box + debounce timer (150 ms — prevents lag on fast typing)
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("بحث بالكود أو الاسم...")
        self._search_box.setLayoutDirection(Qt.RightToLeft)
        self._search_box.setAlignment(Qt.AlignRight)
        self._search_box.setObjectName("codeSearchBox")

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._do_search)
        self._search_box.textChanged.connect(self._on_search_text_changed)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Add custom code button
        add_btn = QPushButton("+ إضافة كود مخصص")
        add_btn.setToolTip("إضافة كود غير موجود في السجل لهذه الجلسة فقط")
        add_btn.clicked.connect(self._on_add_custom)

        title_lbl = QLabel("الأكواد المتاحة")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 800; color: #152433; "
            "background: #FAF0DC; border: 1px solid #D5CFBF; "
            "border-radius: 6px; padding: 4px 12px;"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)
        outer.addWidget(title_lbl)
        outer.addWidget(self._counter_label)
        outer.addWidget(self._search_box)
        outer.addWidget(self._scroll, stretch=1)
        outer.addWidget(add_btn)

        # Track which container is currently shown
        self._current_container: QWidget | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_for_project(
        self,
        project_ids: list[str] | str,
        owner_id: str,
        mandatory_codes: list[str],
    ) -> None:
        """Switch to a project/owner combination."""
        if isinstance(project_ids, str):
            project_ids = [project_ids]

        self._mandatory_codes = set(mandatory_codes)
        self._search_box.clear()
        self._search_timer.stop()

        # ── Slow path: build container from scratch ───────────────────
        self._checkboxes.clear()
        filtered = {
            cid: cdata
            for cid, cdata in self._all_codes.items()
            if (
                cdata.get("status") == "active"
                and any(pid in cdata.get("project_ids", []) for pid in project_ids)
                and (
                    not cdata.get("applicable_owners")
                    or owner_id in cdata.get("applicable_owners", [])
                )
            )
        }
        container = self._build_container(filtered)
        self._reset_to_mandatory_only()

        self._scroll.setWidget(container)
        self._current_container = container
        self._update_counter()

    def _reset_to_mandatory_only(self) -> None:
        """Uncheck all optional items; restore mandatory lock states."""
        for cid, item in self._checkboxes.items():
            is_mandatory = cid in self._mandatory_codes
            is_custom = self._all_codes.get(cid, {}).get("_custom", False)
            item.blockSignals(True)
            item._cb.blockSignals(True)  # Block internal checkbox too
            if is_mandatory:
                item.setChecked(True)
                item.setEnabled(False)
                item.setStyleSheet(_MANDATORY_STYLE)
            elif is_custom:
                item.setChecked(True)
                item.setEnabled(True)
                item.setStyleSheet(_CUSTOM_STYLE)
            else:
                item.setChecked(False)
                item.setEnabled(True)
                cdata = self._all_codes.get(cid, {})
                if "excavation_type" in cdata:
                    item.setStyleSheet(_EXCLUSIVE_STYLE)
                else:
                    item.setStyleSheet("")
            item.setVisible(True)
            item._cb.blockSignals(False)
            item.blockSignals(False)

    def get_selected_codes(self) -> list[str]:
        return [cid for cid, item in self._checkboxes.items() if item.isChecked()]

    def focus_search(self) -> None:
        """Move focus to search and select existing query for quick replacement."""
        self._search_box.setFocus(Qt.ShortcutFocusReason)
        self._search_box.selectAll()

    def add_codes(self, code_ids: list[str]) -> None:
        for cid in code_ids:
            if cid in self._checkboxes and not self._checkboxes[cid].isChecked():
                self._checkboxes[cid].setChecked(True)

    # ------------------------------------------------------------------
    # Container builder
    # ------------------------------------------------------------------

    def _build_container(self, filtered: dict[str, dict]) -> QWidget:
        container = QWidget()
        container.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(6)

        groups: dict[str, list[tuple[int, str, dict]]] = {}
        for cid, cdata in filtered.items():
            cat = cdata.get("category", "001")
            groups.setdefault(cat, [])
            groups[cat].append((_safe_int(cdata.get("sequence_order"), 9999), cid, cdata))

        for cat in sorted(groups):
            codes_in_cat = sorted(groups[cat], key=lambda x: x[0])
            cat_name = _CATEGORY_NAMES.get(cat, cat)
            cat_color, cat_bg = self._category_palette(cat)
            cat_box = QGroupBox()
            cat_box.setLayoutDirection(Qt.RightToLeft)
            cat_box.setProperty("catCode", cat)
            cat_box.setStyleSheet(
                f"QGroupBox {{"
                f"  border: 1px solid {cat_color}55; border-radius: 8px; "
                f"  margin-top: 0; background: {cat_bg}; padding: 0;"
                f"}}"
            )
            cat_layout = QVBoxLayout(cat_box)
            cat_layout.setSpacing(1)
            cat_layout.setContentsMargins(8, 7, 8, 7)

            # Header row: title + select-all / deselect-all buttons
            header = QWidget()
            header.setLayoutDirection(Qt.RightToLeft)
            hlay = QHBoxLayout(header)
            hlay.setContentsMargins(0, 0, 0, 4)
            title_lbl = QLabel(f"{cat} — {cat_name}")
            title_lbl.setStyleSheet(
                f"font-size: 11px; font-weight: bold; color: {cat_color}; "
                f"padding-bottom: 2px; border-bottom: 1px solid {cat_color}33;"
            )
            all_btn = QPushButton("الكل")
            all_btn.setFixedWidth(50)
            all_btn.setStyleSheet(
                f"QPushButton {{"
                f"  font-size:10px; color: {cat_color}; background: #FFFFFFCC; "
                f"  border: 1px solid {cat_color}55; border-radius: 5px; padding: 1px 6px;"
                f"}}"
                f"QPushButton:hover {{ background: {cat_color}20; border-color: {cat_color}; }}"
            )
            none_btn = QPushButton("لا شيء")
            none_btn.setFixedWidth(55)
            none_btn.setStyleSheet(
                f"QPushButton {{"
                f"  font-size:10px; color: #5A6775; background: #FFFFFFCC; "
                f"  border: 1px solid {cat_color}40; border-radius: 5px; padding: 1px 6px;"
                f"}}"
                f"QPushButton:hover {{ background: #F5EFE4; border-color: {cat_color}66; }}"
            )
            hlay.addWidget(title_lbl)
            hlay.addStretch()
            hlay.addWidget(all_btn)
            hlay.addWidget(none_btn)
            cat_layout.addWidget(header)

            cat_items: list[_CodeItem] = []
            for _, cid, cdata in codes_in_cat:
                item = self._make_code_item(cid, cdata)
                cat_layout.addWidget(item)
                self._checkboxes[cid] = item
                cat_items.append(item)

            # Wire select-all / deselect-all to non-mandatory items
            def _select_all(items=cat_items) -> None:
                for it in items:
                    if it.isEnabled():
                        it.setChecked(True)

            def _deselect_all(items=cat_items) -> None:
                for it in items:
                    if it.isEnabled():
                        it.setChecked(False)

            all_btn.clicked.connect(lambda _=None, f=_select_all: f())
            none_btn.clicked.connect(lambda _=None, f=_deselect_all: f())

            layout.addWidget(cat_box)

        return container

    def _category_palette(self, cat: str) -> tuple[str, str]:
        """Return accent and background colors for a category block."""
        return _CATEGORY_COLORS.get(cat, "#4C5C6B"), _CATEGORY_BG.get(cat, "#F5F1E8")

    def _make_code_item(self, code_id: str, code_data: dict) -> _CodeItem:
        name_ar   = code_data.get("activity_name_ar", code_id)
        pages     = _safe_int(code_data.get("page_count"), 0)
        is_custom = code_data.get("_custom", False)

        item = _CodeItem(code_id, name_ar, pages)

        is_mandatory = code_id in self._mandatory_codes
        is_exclusive = "excavation_type" in code_data

        if is_mandatory:
            item.setChecked(True)
            item.setEnabled(False)
            item.setStyleSheet(_MANDATORY_STYLE)
            tip_prefix = "🔒 إلزامي — "
        elif is_custom:
            item.setChecked(True)
            item.setStyleSheet(_CUSTOM_STYLE)
            tip_prefix = "✏️ مخصص — "
        elif is_exclusive:
            item.setStyleSheet(_EXCLUSIVE_STYLE)
            tip_prefix = "⚠️ حصري (اختر نوعاً واحداً) — "
        else:
            tip_prefix = ""

        item.setToolTip(tip_prefix + self._build_tooltip(code_id, code_data))
        item.stateChanged.connect(self._on_checkbox_changed)
        return item

    @staticmethod
    def _build_tooltip(code_id: str, code_data: dict) -> str:
        """Build a rich multi-line tooltip for a code item."""
        name_ar  = code_data.get("activity_name_ar", code_id)
        name_en  = code_data.get("activity_name_en", "")
        pages    = _safe_int(code_data.get("page_count"), 0)
        images   = _safe_int(code_data.get("image_count"), 0)
        deps     = code_data.get("dependencies", [])
        projects = [_PROJECT_NAMES.get(p, p) for p in code_data.get("project_ids", [])]
        owners   = [_OWNER_NAMES.get(o, o)   for o in code_data.get("applicable_owners", [])]

        lines = [f"{code_id}", f"{name_ar}"]
        if name_en:
            lines.append(name_en)
        lines.append("─" * 34)

        page_str = f"📄 {pages} صفحة"
        img_str  = f"   🖼 {images} صورة" if images else ""
        lines.append(page_str + img_str)

        if deps:
            lines.append(f"🔗 يتطلب: {', '.join(deps)}")
        else:
            lines.append("🔗 لا تبعيات")

        if projects:
            lines.append(f"🏗️  {' • '.join(projects)}")
        if owners:
            lines.append(f"🏢  {' • '.join(owners)}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Search — debounced (150 ms)
    # ------------------------------------------------------------------

    def _on_search_text_changed(self, text: str) -> None:
        """Store pending query and restart debounce timer."""
        self._pending_search = text
        self._search_timer.start()   # restart resets the 150 ms countdown

    def _do_search(self) -> None:
        """Execute search after debounce interval."""
        query = self._pending_search.strip().lower()
        for cid, item in self._checkboxes.items():
            cdata = self._all_codes.get(cid, {})
            name  = str(cdata.get("activity_name_ar", "")).lower()
            match = not query or query in cid.lower() or query in name
            item.setVisible(match)

        # Hide category boxes that have no visible items
        if self._current_container:
            for box in self._current_container.findChildren(QGroupBox):
                has_visible = any(
                    c.isVisible()
                    for c in box.findChildren(_CodeItem)
                )
                box.setVisible(has_visible)

    # ------------------------------------------------------------------
    # Add custom code
    # ------------------------------------------------------------------

    def _on_add_custom(self) -> None:
        dialog = _AddCustomCodeDialog(parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        cdata = dialog.get_code_data()
        cid = cdata["code_id"]
        if not cid:
            return
        if cid in self._all_codes:
            # Just check it if already exists
            if cid in self._checkboxes:
                self._checkboxes[cid].setChecked(True)
            return

        # Register temporarily in _all_codes
        # Since we changed the registry data (added a code), we must rebuild.
        # MainWindow already calls refresh in _on_add_custom, but we'll clear search
        self._search_box.clear()
        self._all_codes[cid] = cdata

        cat  = cdata.get("category", "001")
        item = self._make_code_item(cid, cdata)
        self._checkboxes[cid] = item

        # Try to append to the matching category group
        if self._current_container:
            added = False
            for box in self._current_container.findChildren(QGroupBox):
                if str(box.property("catCode") or "") == cat:
                    box.layout().addWidget(item)
                    added = True
                    break
            if not added:
                outer_layout = self._current_container.layout()
                cat_color, cat_bg = self._category_palette(cat)
                new_box = QGroupBox()
                new_box.setLayoutDirection(Qt.RightToLeft)
                new_box.setProperty("catCode", cat)
                new_box.setStyleSheet(
                    f"QGroupBox {{"
                    f"  border: 1px solid {cat_color}55; border-radius: 8px; "
                    f"  margin-top: 0; background: {cat_bg}; padding: 0;"
                    f"}}"
                )
                nb_layout = QVBoxLayout(new_box)
                nb_layout.setContentsMargins(8, 7, 8, 7)
                nb_layout.setSpacing(2)
                title_lbl = QLabel(f"{cat} — {_CATEGORY_NAMES.get(cat, 'مخصص')}")
                title_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: bold; color: {cat_color}; "
                    f"padding-bottom: 2px; border-bottom: 1px solid {cat_color}33;"
                )
                nb_layout.addWidget(title_lbl)
                nb_layout.addWidget(item)
                outer_layout.addWidget(new_box)

        self._update_counter()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _on_checkbox_changed(self) -> None:
        self._update_counter()
        self.codes_changed.emit(self.get_selected_codes())

    def _update_counter(self) -> None:
        selected = self.get_selected_codes()
        total_pages = sum(
            _safe_int(self._all_codes.get(cid, {}).get("page_count"), 0)
            for cid in selected
        )
        self._counter_label.setText(
            f"{len(selected)} أكواد / {total_pages} صفحة تقريباً"
        )


class _AddCustomCodeDialog(QDialog):
    """Quick dialog to define a one-off code not in the registry."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("إضافة كود مخصص")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(430)
        self.setObjectName("addCustomCodeDialog")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        # Enforce a readable palette even if app-level stylesheet sets transparent widgets.
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor("#FEFCF7"))
        pal.setColor(QPalette.WindowText, QColor("#0F2740"))
        pal.setColor(QPalette.Base, QColor("#FFFDFA"))
        pal.setColor(QPalette.Text, QColor("#121B28"))
        self.setPalette(pal)

        # Force readable colors in this dialog regardless of global theme state.
        self.setStyleSheet(
            """
            QDialog#addCustomCodeDialog,
            QDialog#addCustomCodeDialog QWidget {
                background: #FEFCF7;
                color: #121B28;
            }
            QDialog#addCustomCodeDialog QWidget#addCustomCodePanel {
                background: #FEFCF7;
            }
            QDialog#addCustomCodeDialog QLabel {
                color: #FDF7E8;
                background: #1F3A56;
                border: 1px solid #D9B66A;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 700;
                font-size: 13px;
            }
            QDialog#addCustomCodeDialog QLineEdit,
            QDialog#addCustomCodeDialog QSpinBox {
                background: #FFFDFA;
                color: #0E1A29;
                border: 1px solid #C3BBAA;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QDialog#addCustomCodeDialog QLineEdit::placeholder {
                color: #445A72;
            }
            QDialog#addCustomCodeDialog QDialogButtonBox QPushButton {
                min-width: 90px;
            }
            """
        )

        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("مثال: 003-CUSTOM-001")
        self._id_edit.setLayoutDirection(Qt.RightToLeft)
        self._id_edit.setAlignment(Qt.AlignRight)
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("مثال: أعمال خاصة إضافية")
        self._name_edit.setLayoutDirection(Qt.RightToLeft)
        self._name_edit.setAlignment(Qt.AlignRight)
        self._pages_spin = QSpinBox()
        self._pages_spin.setRange(0, 999)
        self._pages_spin.setValue(0)
        self._pages_spin.setAlignment(Qt.AlignRight)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignRight | Qt.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        label_css = (
            "color: #FDF7E8; "
            "background: #1F3A56; "
            "border: 1px solid #D9B66A; "
            "border-radius: 6px; "
            "padding: 4px 10px; "
            "font-weight: 700;"
        )

        id_lbl = QLabel("معرّف الكود:")
        id_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        id_lbl.setStyleSheet(label_css)
        id_lbl.setAutoFillBackground(True)
        form.addRow(id_lbl, self._id_edit)

        name_lbl = QLabel("الاسم بالعربية:")
        name_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        name_lbl.setStyleSheet(label_css)
        name_lbl.setAutoFillBackground(True)
        form.addRow(name_lbl, self._name_edit)

        pages_lbl = QLabel("عدد الصفحات التقديري:")
        pages_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pages_lbl.setStyleSheet(label_css)
        pages_lbl.setAutoFillBackground(True)
        form.addRow(pages_lbl, self._pages_spin)

        panel = QWidget(self)
        panel.setObjectName("addCustomCodePanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setAutoFillBackground(True)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 6, 8, 6)
        panel_layout.setSpacing(10)
        panel_layout.addLayout(form)
        panel_layout.addWidget(buttons)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(panel)

    def get_code_data(self) -> dict:
        cid = self._id_edit.text().strip()
        cat = cid.split("-")[0] if "-" in cid else "001"
        return {
            "code_id": cid,
            "activity_name_ar": self._name_edit.text().strip() or cid,
            "activity_name_en": "",
            "category": cat,
            "status": "active",
            "project_ids": [],
            "applicable_owners": [],
            "sequence_order": 9999,
            "page_count": self._pages_spin.value(),
            "image_count": 0,
            "dependencies": [],
            "_custom": True,
        }
