#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-002 (v2): Project multi-select checkboxes + owner selector + admin add-owner.

- Projects shown as checkboxes (multi-select) — proposal can span multiple project types.
- Owner combo filtered to union of applicable owners for all checked projects.
- "+" button next to owner → admin password dialog → add new owner to master_config.json.
- Emits selection_changed(list[str], str) → (project_ids, owner_id).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Admin password SHA-256 hash — default: "rawaf2024"
# Change by running: hashlib.sha256(b"your_password").hexdigest()
_DEFAULT_ADMIN_HASH = hashlib.sha256(b"rawaf2024").hexdigest()
_CONFIG_PATH = Path("master_config.json")
_PROJECT_COLORS: dict[str, str] = {
    "wastewater": "#1F5B8E",
    "water_supply": "#2E7399",
    "water_transmission": "#3A618F",
    "asphalt": "#A4641E",
    "road_maintenance": "#B1742A",
    "general_construction": "#4C6E5A",
}


def _safe_int(value: Any, default: int = 0) -> int:
    """Parse int safely; fallback to default on invalid values."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_page_range(value: Any) -> tuple[int, int]:
    """Return a safe (min,max) page range tuple from mixed config formats."""
    if isinstance(value, (list, tuple)):
        if len(value) >= 2:
            return _safe_int(value[0], 0), _safe_int(value[1], 0)
        if len(value) == 1:
            one = _safe_int(value[0], 0)
            return one, one
    if isinstance(value, str) and "-" in value:
        left, right = value.split("-", 1)
        return _safe_int(left.strip(), 0), _safe_int(right.strip(), 0)
    if isinstance(value, (int, float, str)):
        one = _safe_int(value, 0)
        return one, one
    return 0, 0


class ProjectSelectorWidget(QGroupBox):
    """Multi-project checkboxes + owner dropdown with admin add-owner."""

    # Emits (list[str] project_ids, str owner_id)
    selection_changed = pyqtSignal(list, str)

    def __init__(self, config_data: dict[str, Any], parent=None) -> None:
        super().__init__("", parent)
        self.setLayoutDirection(Qt.RightToLeft)

        self._config_data = config_data
        self._projects: dict[str, dict] = config_data.get("projects", {})
        self._owners: dict[str, dict] = config_data.get("owner_specifications", {})
        self._admin_hash: str = config_data.get(
            "admin_settings", {}
        ).get("password_hash", _DEFAULT_ADMIN_HASH)

        self._project_checks: dict[str, QCheckBox] = {}
        self._owner_combo = QComboBox()
        self._owner_combo.setMinimumWidth(220)
        self._owner_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self._info_label = QLabel("")
        self._info_label.setWordWrap(True)

        self._build_layout()
        self._populate_projects()
        self._owner_combo.currentIndexChanged.connect(self._on_owner_changed)
        # Explicit refresh — ensures owners show even if stateChanged didn't fire
        self._refresh_owners()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(9)

        title_lbl = QLabel("اختيار المشروع والجهة المالكة")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 800; color: #152433; "
            "background: #FAF0DC; border: 1px solid #D5CFBF; "
            "border-radius: 6px; padding: 4px 12px;"
        )
        root.addWidget(title_lbl)

        outer = QFormLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setHorizontalSpacing(14)
        outer.setVerticalSpacing(8)
        outer.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        root.addLayout(outer)

        def _form_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setMinimumWidth(92)
            label.setStyleSheet(
                "font-weight: 700; color: #152433; "
                "background: transparent; padding: 2px 0;"
            )
            return label

        # Projects: horizontal wrap of checkboxes
        proj_widget = QWidget()
        proj_widget.setLayoutDirection(Qt.RightToLeft)
        proj_layout = QHBoxLayout(proj_widget)
        proj_layout.setContentsMargins(0, 0, 0, 0)
        proj_layout.setSpacing(12)
        self._proj_layout = proj_layout
        outer.addRow(_form_label("المشاريع:"), proj_widget)

        # Owner: combo + add button
        owner_row = QWidget()
        owner_row.setLayoutDirection(Qt.RightToLeft)
        owner_h = QHBoxLayout(owner_row)
        owner_h.setContentsMargins(0, 0, 0, 0)
        owner_h.addWidget(self._owner_combo, stretch=1)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.setToolTip("إضافة جهة مالكة جديدة (للمشرف فقط)")
        add_btn.clicked.connect(self._on_add_owner)
        owner_h.addWidget(add_btn)
        outer.addRow(_form_label("الجهة المالكة:"), owner_row)

        outer.addRow(self._info_label)

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _populate_projects(self) -> None:
        for pid, pdata in self._projects.items():
            label = pdata.get("name_ar") or pid
            cb = QCheckBox(label)
            cb.setLayoutDirection(Qt.RightToLeft)
            accent = _PROJECT_COLORS.get(pid, "#1B2D40")
            cb.setStyleSheet(
                f"QCheckBox {{ color: {accent}; font-weight: 600; }}"
                f"QCheckBox::indicator:checked {{ "
                f"background: {accent}; border-color: {accent}; "
                f"}}"
            )
            cb.stateChanged.connect(self._on_projects_changed)
            self._project_checks[pid] = cb
            self._proj_layout.addWidget(cb)
        self._proj_layout.addStretch()
        # Select first project by default
        if self._project_checks:
            first = next(iter(self._project_checks.values()))
            first.setChecked(True)

    def _refresh_owners(self) -> None:
        selected_pids = self.current_project_ids()
        # Union of applicable owners across all checked projects
        applicable: list[str] = []
        seen: set[str] = set()
        for pid in selected_pids:
            for oid in self._projects.get(pid, {}).get("applicable_owners", []):
                if oid not in seen:
                    applicable.append(oid)
                    seen.add(oid)

        self._owner_combo.blockSignals(True)
        self._owner_combo.clear()
        if applicable:
            for oid in applicable:
                odata = self._owners.get(oid, {})
                label = odata.get("owner_name_ar") or oid
                self._owner_combo.addItem(label, userData=oid)
            self._owner_combo.setEnabled(True)
        else:
            self._owner_combo.addItem("لا توجد جهة مالكة متاحة", userData="")
            self._owner_combo.setEnabled(False)
        self._owner_combo.blockSignals(False)

        self._update_info_label()
        self._emit_current()

    def _update_info_label(self) -> None:
        pids = self.current_project_ids()
        if not pids:
            self._info_label.setText("")
            return
        lines: list[str] = []
        for pid in pids:
            pdata = self._projects.get(pid, {})
            desc = pdata.get("description_ar", "")
            min_pages, max_pages = _normalize_page_range(pdata.get("typical_page_range"))
            if desc:
                lines.append(
                    f"<b>{pdata.get('name_ar', pid)}:</b> "
                    f"{desc} ({min_pages}–{max_pages} صفحة)"
                )
        self._info_label.setText(
            "<small>" + "<br>".join(lines) + "</small>" if lines else ""
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_project_ids(self) -> list[str]:
        return [pid for pid, cb in self._project_checks.items() if cb.isChecked()]

    def current_owner_id(self) -> str:
        return str(self._owner_combo.currentData() or "").strip()

    def apply_preset(self, project_ids: list[str], owner_id: str) -> None:
        """Set project checkboxes and owner combo to match the given preset values.

        Blocks intermediate signals so the checkbox list is only rebuilt once
        (after both project IDs and owner are already set).
        """
        # Block all signals to prevent multiple rebuilds during batch update
        for cb in self._project_checks.values():
            cb.blockSignals(True)
        self._owner_combo.blockSignals(True)

        # Keep only known project ids; fallback to first project to avoid empty state.
        valid_project_ids = [pid for pid in project_ids if pid in self._project_checks]
        if not valid_project_ids and self._project_checks:
            valid_project_ids = [next(iter(self._project_checks))]

        # Set project checkboxes
        for pid, cb in self._project_checks.items():
            cb.setChecked(pid in valid_project_ids)

        # Rebuild owner list for the new project selection
        applicable: list[str] = []
        seen: set[str] = set()
        for pid in valid_project_ids:
            for oid in self._projects.get(pid, {}).get("applicable_owners", []):
                if oid not in seen:
                    applicable.append(oid)
                    seen.add(oid)

        self._owner_combo.clear()
        if applicable:
            for oid in applicable:
                odata = self._owners.get(oid, {})
                label = odata.get("owner_name_ar") or oid
                self._owner_combo.addItem(label, userData=oid)
            self._owner_combo.setEnabled(True)
        else:
            self._owner_combo.addItem("لا توجد جهة مالكة متاحة", userData="")
            self._owner_combo.setEnabled(False)

        # Select the target owner; fallback to first available owner.
        target_idx = -1
        for i in range(self._owner_combo.count()):
            if str(self._owner_combo.itemData(i) or "") == owner_id:
                target_idx = i
                break
        if target_idx >= 0:
            self._owner_combo.setCurrentIndex(target_idx)
        elif self._owner_combo.count() > 0:
            self._owner_combo.setCurrentIndex(0)

        # Unblock and fire a single update
        for cb in self._project_checks.values():
            cb.blockSignals(False)
        self._owner_combo.blockSignals(False)

        self._update_info_label()
        self._emit_current()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_projects_changed(self) -> None:
        self._refresh_owners()

    def _on_owner_changed(self, _index: int) -> None:
        self._update_info_label()
        self._emit_current()

    def _emit_current(self) -> None:
        pids = self.current_project_ids()
        oid = self.current_owner_id()
        # Emit even if empty/invalid — allows Main to clear dependent UI (BKL-009)
        self.selection_changed.emit(pids, oid)

    # ------------------------------------------------------------------
    # Admin: Add Owner
    # ------------------------------------------------------------------

    def _on_add_owner(self) -> None:
        # Step 1: password
        pwd, ok = QInputDialog.getText(
            self, "كلمة السر", "أدخل كلمة سر المشرف:",
            QLineEdit.Password
        )
        if not ok or not pwd:
            return
        if hashlib.sha256(pwd.encode()).hexdigest() != self._admin_hash:
            QMessageBox.critical(self, "خطأ", "كلمة السر غير صحيحة.")
            return

        # Step 2: owner details dialog
        dialog = _AddOwnerDialog(self._projects, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return

        owner_data = dialog.get_owner_data()
        owner_id = owner_data["owner_id"]

        if not owner_id:
            QMessageBox.warning(self, "تحذير", "معرّف الجهة لا يمكن أن يكون فارغاً.")
            return
        if not owner_data["owner_name_ar"]:
            QMessageBox.warning(self, "تحذير", "اسم الجهة لا يمكن أن يكون فارغاً.")
            return
        if not owner_data["project_ids"]:
            QMessageBox.warning(self, "تحذير", "اختر مشروعاً واحداً على الأقل لربط الجهة.")
            return

        # Save to config
        self._config_data.setdefault("owner_specifications", {})[owner_id] = {
            "owner_id": owner_id,
            "owner_name_ar": owner_data["owner_name_ar"],
            "applicable_networks": owner_data["applicable_networks"],
            "mandatory_codes": [],
            "forbidden_codes": [],
        }

        # Add owner to applicable_owners of checked projects
        for pid in owner_data["project_ids"]:
            proj = self._config_data.get("projects", {}).get(pid, {})
            ao = proj.setdefault("applicable_owners", [])
            if owner_id not in ao:
                ao.append(owner_id)

        # Persist to master_config.json
        try:
            _CONFIG_PATH.write_text(
                json.dumps(self._config_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as exc:
            QMessageBox.warning(self, "تحذير", f"تعذّر حفظ التغييرات: {exc}")
            return

        # Refresh internal state
        self._owners = self._config_data["owner_specifications"]
        self._refresh_owners()
        QMessageBox.information(
            self, "تم", f"تمت إضافة الجهة '{owner_data['owner_name_ar']}' بنجاح."
        )


class _AddOwnerDialog(QDialog):
    """Dialog for entering new owner details."""

    def __init__(self, projects: dict[str, dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("إضافة جهة مالكة جديدة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(400)

        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("مثال: new_authority")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("مثال: الجهة الجديدة للمشاريع")
        self._networks_edit = QLineEdit()
        self._networks_edit.setPlaceholderText("مثال: S, W")

        # Project checkboxes
        self._proj_checks: dict[str, QCheckBox] = {}
        proj_group = QGroupBox("ربط بالمشاريع")
        proj_group.setLayoutDirection(Qt.RightToLeft)
        proj_layout = QVBoxLayout(proj_group)
        for pid, pdata in projects.items():
            cb = QCheckBox(pdata.get("name_ar", pid))
            cb.setLayoutDirection(Qt.RightToLeft)
            self._proj_checks[pid] = cb
            proj_layout.addWidget(cb)

        form = QFormLayout()
        form.addRow("معرّف الجهة (بالإنجليزية):", self._id_edit)
        form.addRow("اسم الجهة (بالعربية):", self._name_edit)
        form.addRow("أنواع الشبكات:", self._networks_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(proj_group)
        layout.addWidget(buttons)

    def get_owner_data(self) -> dict:
        return {
            "owner_id": self._id_edit.text().strip().lower().replace(" ", "_"),
            "owner_name_ar": self._name_edit.text().strip(),
            "applicable_networks": [
                n.strip().upper()
                for n in self._networks_edit.text().split(",")
                if n.strip()
            ],
            "project_ids": [
                pid for pid, cb in self._proj_checks.items() if cb.isChecked()
            ],
        }
