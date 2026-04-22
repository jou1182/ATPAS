#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-012: Import Wizard — two-tab dialog.

Tab 1 — استيراد أكواد:
    • اختر ملفات Word (.docx) أو أضف كوداً يدوياً
    • لكل ملف: يُقترح معرّف الكود واسمه من محتوى الوثيقة
    • عند التأكيد: ينسخ الملف إلى templates/source_documents/
      ويُحدّث codes_registry.json

Tab 2 — إدارة الجهات:
    • عرض الجهات الموجودة / تعديلها / إضافة جديدة
    • يُحدّث master_config.json + metadata/owner_specifications/
      + templates/style_templates/ (ملف نمط أساسي)
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# ── ثوابت ──────────────────────────────────────────────────────────────────
_SOURCE_DOCS_DIR   = Path("templates/source_documents")
_STYLE_TMPL_DIR    = Path("templates/style_templates")
_OWNER_META_DIR    = Path("metadata/owner_specifications")
_REGISTRY_PATH     = Path("codes_registry.json")
_CONFIG_PATH       = Path("master_config.json")

_PROJECTS: list[tuple[str, str]] = [
    ("wastewater",           "نظام الصرف الصحي"),
    ("water_supply",         "نظام إمدادات المياه"),
    ("asphalt",              "نظام الطرق والأسفلت"),
    ("road_maintenance",     "صيانة الطرق والأرصفة"),
    ("general_construction", "الإنشاءات العامة والمرافق"),
    ("water_transmission",   "خطوط نقل المياه الرئيسية"),
]

_NETWORKS: list[tuple[str, str]] = [
    ("S", "صرف صحي  (S)"),
    ("W", "مياه شرب  (W)"),
    ("A", "أسفلت  (A)"),
    ("R", "طرق  (R)"),
    ("C", "إنشاءات  (C)"),
    ("T", "ناقل مياه  (T)"),
]

_CATEGORIES: list[tuple[str, str]] = [
    ("001", "001 — الأعمال التحضيرية"),
    ("002", "002 — الحفر والمخلفات"),
    ("003", "003 — التركيب والتوصيل"),
    ("004", "004 — الاختبارات والفحوصات"),
    ("005", "005 — الإنهاء والتسليم"),
]

_BTN_PRIMARY = """
    QPushButton {
        background: #152433; color: #C9921B;
        border: none; border-radius: 6px;
        font-size: 12px; font-weight: 700;
        padding: 6px 18px;
    }
    QPushButton:hover  { background: #1C3045; }
    QPushButton:pressed{ background: #0D1C2B; }
    QPushButton:disabled { background: #B0A898; color: #7A706A; }
"""
_BTN_SECONDARY = """
    QPushButton {
        background: #F0EDE6; color: #3A4A5A;
        border: 1px solid #C8C0B0; border-radius: 5px;
        font-size: 11px; padding: 5px 14px;
    }
    QPushButton:hover { background: #E5E0D8; }
"""
_BTN_DANGER = """
    QPushButton {
        background: #FFEBEE; color: #C62828;
        border: 1px solid #FFCDD2; border-radius: 5px;
        font-size: 11px; padding: 5px 14px;
    }
    QPushButton:hover { background: #FFCDD2; }
"""


# ─────────────────────────────────────────────────────────────────────────────
# نافذة الاختيار المتعدد
# ─────────────────────────────────────────────────────────────────────────────

class _MultiSelectDialog(QDialog):
    """نافذة خانات اختيار متعددة — تُعيد قائمة المُختارين."""

    def __init__(
        self,
        title: str,
        options: list[tuple[str, str]],   # [(id, label), ...]
        selected: list[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        self._checks: dict[str, QCheckBox] = {}
        for opt_id, opt_label in options:
            cb = QCheckBox(opt_label)
            cb.setChecked(opt_id in selected)
            cb.setLayoutDirection(Qt.RightToLeft)
            layout.addWidget(cb)
            self._checks[opt_id] = cb

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_ids(self) -> list[str]:
        return [k for k, cb in self._checks.items() if cb.isChecked()]


# ─────────────────────────────────────────────────────────────────────────────
# صف استيراد كود واحد
# ─────────────────────────────────────────────────────────────────────────────

class _CodeImportRow(QFrame):
    """صف واحد في قائمة استيراد الأكواد."""

    remove_requested = pyqtSignal(object)   # self

    def __init__(
        self,
        file_path: Path | None,
        owner_options: list[tuple[str, str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._owner_options = owner_options
        self._selected_projects: list[str] = []
        self._selected_owners:   list[str] = []

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #FEFCF8;
                border: 1px solid #DDD8CC;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # ── اسم الملف ──────────────────────────────────────────────────
        if file_path:
            file_lbl = QLabel(f"📄 {file_path.name}")
            file_lbl.setLayoutDirection(Qt.LeftToRight)
            file_lbl.setAlignment(Qt.AlignLeft)
            file_lbl.setStyleSheet(
                "font-size: 10px; color: #5A6A7A; "
                "background: #EEF3FA; border-radius: 4px; padding: 2px 6px;"
            )
            layout.addWidget(file_lbl)

        # ── الحقول الرئيسية ─────────────────────────────────────────────
        form = QHBoxLayout()
        form.setSpacing(8)

        # معرّف الكود
        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("معرّف الكود  مثال: 003-PIP-MAIN")
        self._id_edit.setMinimumWidth(160)
        self._id_edit.setLayoutDirection(Qt.LeftToRight)
        self._id_edit.setAlignment(Qt.AlignLeft)
        if file_path:
            self._id_edit.setText(file_path.stem)

        # الاسم العربي
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("الاسم العربي للنشاط")
        self._name_edit.setLayoutDirection(Qt.RightToLeft)
        self._name_edit.setAlignment(Qt.AlignRight)
        self._name_edit.setMinimumWidth(200)
        if file_path:
            self._name_edit.setText(_read_doc_title(file_path))

        # التصنيف
        self._cat_combo = QComboBox()
        self._cat_combo.setLayoutDirection(Qt.RightToLeft)
        for cat_id, cat_label in _CATEGORIES:
            self._cat_combo.addItem(cat_label, cat_id)
        if file_path:
            # اقتراح التصنيف من بادئة اسم الملف
            stem = file_path.stem
            for cat_id, _ in _CATEGORIES:
                if stem.startswith(cat_id):
                    idx = self._cat_combo.findData(cat_id)
                    if idx >= 0:
                        self._cat_combo.setCurrentIndex(idx)
                    break

        # الصفحات
        self._pages_spin = QSpinBox()
        self._pages_spin.setRange(0, 999)
        self._pages_spin.setValue(_estimate_pages(file_path) if file_path else 0)
        self._pages_spin.setSuffix(" ص")
        self._pages_spin.setFixedWidth(70)
        self._pages_spin.setAlignment(Qt.AlignCenter)

        form.addWidget(self._id_edit,    2)
        form.addWidget(self._name_edit,  3)
        form.addWidget(self._cat_combo,  2)
        form.addWidget(self._pages_spin, 0)
        layout.addLayout(form)

        # ── صف الأزرار الثانوية ──────────────────────────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self._proj_btn = QPushButton("🏗️  المشاريع (0)")
        self._proj_btn.setStyleSheet(_BTN_SECONDARY)
        self._proj_btn.setCursor(Qt.PointingHandCursor)
        self._proj_btn.clicked.connect(self._pick_projects)

        self._owner_btn = QPushButton("🏢  الجهات (0)")
        self._owner_btn.setStyleSheet(_BTN_SECONDARY)
        self._owner_btn.setCursor(Qt.PointingHandCursor)
        self._owner_btn.clicked.connect(self._pick_owners)

        del_btn = QPushButton("✕")
        del_btn.setFixedWidth(32)
        del_btn.setStyleSheet(_BTN_DANGER)
        del_btn.setToolTip("حذف هذا الصف")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.remove_requested.emit(self))

        row2.addWidget(self._proj_btn)
        row2.addWidget(self._owner_btn)
        row2.addStretch()
        row2.addWidget(del_btn)
        layout.addLayout(row2)

    # ── pickers ─────────────────────────────────────────────────────────

    def _pick_projects(self) -> None:
        dlg = _MultiSelectDialog(
            "اختر المشاريع المناسبة", _PROJECTS, self._selected_projects, self
        )
        if dlg.exec_() == QDialog.Accepted:
            self._selected_projects = dlg.selected_ids()
            self._proj_btn.setText(f"🏗️  المشاريع ({len(self._selected_projects)})")

    def _pick_owners(self) -> None:
        dlg = _MultiSelectDialog(
            "اختر الجهات المالكة", self._owner_options, self._selected_owners, self
        )
        if dlg.exec_() == QDialog.Accepted:
            self._selected_owners = dlg.selected_ids()
            self._owner_btn.setText(f"🏢  الجهات ({len(self._selected_owners)})")

    # ── public API ───────────────────────────────────────────────────────

    def code_id(self) -> str:
        return self._id_edit.text().strip()

    def validate(self) -> str:
        """يُعيد رسالة خطأ أو سلسلة فارغة إذا كان الصف صحيحاً."""
        if not self.code_id():
            return "معرّف الكود مطلوب"
        if not self._name_edit.text().strip():
            return f"[{self.code_id()}] الاسم العربي مطلوب"
        if not self._selected_projects:
            return f"[{self.code_id()}] اختر مشروعاً واحداً على الأقل"
        return ""

    def to_code_dict(self) -> dict:
        cid = self.code_id()
        cat = self._cat_combo.currentData() or "001"
        today = date.today().isoformat()
        return {
            "code_id":          cid,
            "category":         cat,
            "phase":            cid.split("-")[1] if "-" in cid else "GEN",
            "variation":        cid.split("-")[2] if cid.count("-") >= 2 else "BASE",
            "activity_name_ar": self._name_edit.text().strip(),
            "activity_name_en": "",
            "project_ids":      self._selected_projects,
            "network_types":    [],
            "applicable_owners": self._selected_owners,
            "sequence_order":   9999,
            "dependencies":     [],
            "has_images":       False,
            "image_count":      0,
            "page_count":       self._pages_spin.value(),
            "source_document":  f"{cid}.docx" if self._file_path else "",
            "section_reference":"",
            "tags":             [],
            "status":           "active",
            "created_date":     today,
            "last_modified":    today,
            "version":          "1.0",
            "notes":            "",
        }

    def source_file(self) -> Path | None:
        return self._file_path


# ─────────────────────────────────────────────────────────────────────────────
# Tab 1 — استيراد أكواد
# ─────────────────────────────────────────────────────────────────────────────

class _ImportCodesTab(QWidget):
    """تبويب استيراد الأكواد من ملفات Word."""

    # يُطلق بعد الاستيراد الناجح مع عدد الأكواد المُضافة
    codes_imported = pyqtSignal(int)

    def __init__(self, registry_data: dict, config_data: dict, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._registry_data = registry_data
        self._rows: list[_CodeImportRow] = []

        # قائمة الجهات لعرضها في نافذة الاختيار
        self._owner_options = self._build_owner_options(config_data)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(8)

        # ── شريط الأزرار العلوي ─────────────────────────────────────────
        top_bar = QHBoxLayout()
        pick_btn = QPushButton("📂  اختر ملفات Word (.docx)...")
        pick_btn.setStyleSheet(_BTN_PRIMARY)
        pick_btn.setCursor(Qt.PointingHandCursor)
        pick_btn.clicked.connect(self._pick_files)

        manual_btn = QPushButton("✏️  إضافة يدوية بدون ملف")
        manual_btn.setStyleSheet(_BTN_SECONDARY)
        manual_btn.setCursor(Qt.PointingHandCursor)
        manual_btn.clicked.connect(self._add_manual_row)

        top_bar.addWidget(pick_btn)
        top_bar.addWidget(manual_btn)
        top_bar.addStretch()
        outer.addLayout(top_bar)

        # ── تلميح ──────────────────────────────────────────────────────
        hint = QLabel(
            "📋 يُستخرج اسم الكود تلقائياً من عنوان الوثيقة — راجع وعدّل قبل الاستيراد"
        )
        hint.setStyleSheet("color: #6A7A8A; font-size: 11px;")
        hint.setAlignment(Qt.AlignRight)
        outer.addWidget(hint)

        # ── منطقة الصفوف القابلة للتمرير ───────────────────────────────
        self._rows_widget = QWidget()
        self._rows_widget.setLayoutDirection(Qt.RightToLeft)
        self._rows_layout = QVBoxLayout(self._rows_widget)
        self._rows_layout.setAlignment(Qt.AlignTop)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)

        self._empty_lbl = QLabel("لم يتم اختيار أي ملف بعد — اضغط «اختر ملفات» للبدء")
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #9BA8B5; font-size: 13px; padding: 40px;")
        self._rows_layout.addWidget(self._empty_lbl)

        scroll = QScrollArea()
        scroll.setWidget(self._rows_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: #F8F5EE;")
        outer.addWidget(scroll, 1)

        # ── شريط الأزرار السفلي ─────────────────────────────────────────
        bottom_bar = QHBoxLayout()
        self._counter_lbl = QLabel("0 كود جاهز للاستيراد")
        self._counter_lbl.setStyleSheet("color: #4A5A6A; font-size: 11px;")

        self._import_btn = QPushButton("✅  استيراد الكل")
        self._import_btn.setStyleSheet(_BTN_PRIMARY)
        self._import_btn.setCursor(Qt.PointingHandCursor)
        self._import_btn.setEnabled(False)
        self._import_btn.clicked.connect(self._do_import)

        bottom_bar.addWidget(self._counter_lbl)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self._import_btn)
        outer.addLayout(bottom_bar)

    # ── helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_owner_options(config_data: dict) -> list[tuple[str, str]]:
        """بناء قائمة الجهات من ملفات الميتاداتا."""
        options: list[tuple[str, str]] = []
        for owner_file in sorted(_OWNER_META_DIR.glob("*.json")):
            try:
                with open(owner_file, encoding="utf-8") as f:
                    data = json.load(f)
                oid   = data.get("owner_id", owner_file.stem)
                label = data.get("owner_name_ar", oid)
                options.append((oid, label))
            except Exception:
                options.append((owner_file.stem, owner_file.stem))
        return options

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "اختر ملفات Word",
            str(Path(".")), "Word Files (*.docx *.doc)"
        )
        for p in paths:
            self._add_row(Path(p))

    def _add_manual_row(self) -> None:
        self._add_row(None)

    def _add_row(self, path: Path | None) -> None:
        if self._empty_lbl.isVisible():
            self._empty_lbl.setVisible(False)

        row = _CodeImportRow(path, self._owner_options, self._rows_widget)
        row.remove_requested.connect(self._remove_row)
        self._rows.append(row)
        self._rows_layout.addWidget(row)
        self._refresh_counter()

    def _remove_row(self, row: _CodeImportRow) -> None:
        self._rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        if not self._rows:
            self._empty_lbl.setVisible(True)
        self._refresh_counter()

    def _refresh_counter(self) -> None:
        n = len(self._rows)
        self._counter_lbl.setText(f"{n} كود جاهز للاستيراد")
        self._import_btn.setEnabled(n > 0)

    # ── import logic ─────────────────────────────────────────────────────

    def _do_import(self) -> None:
        # التحقق من صحة جميع الصفوف
        errors: list[str] = []
        existing_ids = set(self._registry_data.get("codes", {}).keys())
        seen_ids: set[str] = set()

        for row in self._rows:
            err = row.validate()
            if err:
                errors.append(err)
                continue
            cid = row.code_id()
            if cid in existing_ids:
                errors.append(f"[{cid}] موجود بالفعل في السجل — استخدم معرّفاً مختلفاً")
            elif cid in seen_ids:
                errors.append(f"[{cid}] مكرر في القائمة الحالية")
            else:
                seen_ids.add(cid)

        if errors:
            QMessageBox.warning(
                self, "تحقق من البيانات",
                "يرجى تصحيح الأخطاء التالية:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
            return

        # الاستيراد
        imported = 0
        failed: list[str] = []
        codes_dict: dict = self._registry_data.setdefault("codes", {})

        for row in list(self._rows):
            cid = row.code_id()
            src = row.source_file()

            # نسخ ملف Word إذا وُجد
            if src and src.exists():
                dest = _SOURCE_DOCS_DIR / f"{cid}.docx"
                try:
                    _SOURCE_DOCS_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest)
                except Exception as exc:
                    failed.append(f"{cid}: فشل نسخ الملف — {exc}")
                    continue

            # إضافة الكود إلى السجل
            codes_dict[cid] = row.to_code_dict()
            imported += 1

        if imported == 0:
            QMessageBox.warning(self, "خطأ", "لم يتم استيراد أي كود.")
            return

        # حفظ codes_registry.json
        self._registry_data["metadata"]["total_codes"] = len(codes_dict)
        try:
            with open(_REGISTRY_PATH, "w", encoding="utf-8") as f:
                json.dump(self._registry_data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            QMessageBox.critical(self, "خطأ في الحفظ", f"تعذّر حفظ السجل:\n{exc}")
            return

        # مسح الصفوف المُستوردة
        for row in list(self._rows):
            self._remove_row(row)

        msg = f"✅ تم استيراد {imported} كود بنجاح."
        if failed:
            msg += "\n\nتحذيرات:\n" + "\n".join(f"• {e}" for e in failed)
        QMessageBox.information(self, "اكتمل الاستيراد", msg)
        self.codes_imported.emit(imported)


# ─────────────────────────────────────────────────────────────────────────────
# Tab 2 — إدارة الجهات
# ─────────────────────────────────────────────────────────────────────────────

class _OwnersTab(QWidget):
    """تبويب إضافة وتعديل الجهات المالكة."""

    owner_saved = pyqtSignal()

    def __init__(self, config_data: dict, registry_data: dict, parent=None) -> None:
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._config_data   = config_data
        self._registry_data = registry_data
        self._editing_id: str | None = None     # None = جديد

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        # ── قائمة الجهات الموجودة ────────────────────────────────────────
        left = QVBoxLayout()
        lbl = QLabel("الجهات الموجودة")
        lbl.setStyleSheet("font-weight: bold; color: #152433;")
        lbl.setAlignment(Qt.AlignRight)

        self._owner_list = QListWidget()
        self._owner_list.setLayoutDirection(Qt.RightToLeft)
        self._owner_list.setMinimumWidth(180)
        self._owner_list.setMaximumWidth(220)
        self._owner_list.currentItemChanged.connect(self._on_owner_selected)
        self._refresh_owner_list()

        new_btn = QPushButton("＋  إضافة جهة جديدة")
        new_btn.setStyleSheet(_BTN_PRIMARY)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._new_owner)

        left.addWidget(lbl)
        left.addWidget(self._owner_list, 1)
        left.addWidget(new_btn)
        outer.addLayout(left)

        # ── فاصل ────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #DDD8CC;")
        outer.addWidget(sep)

        # ── نموذج البيانات ────────────────────────────────────────────────
        right = QVBoxLayout()
        self._form_title = QLabel("اختر جهةً أو أضف جديدةً")
        self._form_title.setStyleSheet(
            "font-size: 14px; font-weight: 800; color: #152433;"
            " border-bottom: 2px solid #C9921B; padding-bottom: 4px;"
        )
        self._form_title.setAlignment(Qt.AlignRight)
        right.addWidget(self._form_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        def _lbl(text: str) -> QLabel:
            lb = QLabel(text)
            lb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lb.setStyleSheet("font-weight: 600; color: #2A3A4A;")
            return lb

        self._fid   = QLineEdit(); self._fid.setPlaceholderText("مثال: my_owner")
        self._fid.setLayoutDirection(Qt.LeftToRight)
        self._fid.setAlignment(Qt.AlignLeft)

        self._far   = QLineEdit(); self._far.setPlaceholderText("مثال: أمانة منطقة تبوك")
        self._far.setLayoutDirection(Qt.RightToLeft); self._far.setAlignment(Qt.AlignRight)

        self._fen   = QLineEdit(); self._fen.setPlaceholderText("مثال: Tabuk Municipality")
        self._fen.setLayoutDirection(Qt.LeftToRight); self._fen.setAlignment(Qt.AlignLeft)

        self._fcode = QLineEdit(); self._fcode.setPlaceholderText("مثال: TAB")
        self._fcode.setLayoutDirection(Qt.LeftToRight); self._fcode.setAlignment(Qt.AlignLeft)
        self._fcode.setMaximumWidth(100)

        self._fcontact = QLineEdit(); self._fcontact.setPlaceholderText("البريد الإلكتروني")
        self._fcontact.setLayoutDirection(Qt.LeftToRight); self._fcontact.setAlignment(Qt.AlignLeft)

        form.addRow(_lbl("المعرّف (ID):"),        self._fid)
        form.addRow(_lbl("الاسم بالعربية:"),      self._far)
        form.addRow(_lbl("الاسم بالإنجليزية:"),   self._fen)
        form.addRow(_lbl("الرمز المختصر:"),        self._fcode)
        form.addRow(_lbl("جهة الاتصال:"),          self._fcontact)
        right.addLayout(form)

        # الشبكات
        net_box = QGroupBox("الشبكات المناسبة")
        net_box.setLayoutDirection(Qt.RightToLeft)
        net_box.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #2A3A4A; "
            "border: 1px solid #C8C0B0; border-radius: 6px; padding: 4px; }"
        )
        net_layout = QHBoxLayout(net_box)
        self._net_checks: dict[str, QCheckBox] = {}
        for nid, nlabel in _NETWORKS:
            cb = QCheckBox(nlabel)
            cb.setLayoutDirection(Qt.RightToLeft)
            self._net_checks[nid] = cb
            net_layout.addWidget(cb)
        right.addWidget(net_box)

        # الأكواد الإلزامية
        mand_row = QHBoxLayout()
        self._mand_btn = QPushButton("🔒  الأكواد الإلزامية (0)")
        self._mand_btn.setStyleSheet(_BTN_SECONDARY)
        self._mand_btn.setCursor(Qt.PointingHandCursor)
        self._mand_btn.clicked.connect(self._pick_mandatory)
        self._mandatory_codes: list[str] = []
        mand_row.addWidget(self._mand_btn)
        mand_row.addStretch()
        right.addLayout(mand_row)

        right.addStretch()

        # أزرار الحفظ والحذف
        btn_row = QHBoxLayout()
        self._save_btn = QPushButton("💾  حفظ الجهة")
        self._save_btn.setStyleSheet(_BTN_PRIMARY)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._do_save_owner)

        self._del_btn = QPushButton("🗑  حذف")
        self._del_btn.setStyleSheet(_BTN_DANGER)
        self._del_btn.setCursor(Qt.PointingHandCursor)
        self._del_btn.clicked.connect(self._do_delete_owner)
        self._del_btn.setVisible(False)

        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._del_btn)
        btn_row.addStretch()
        right.addLayout(btn_row)

        outer.addLayout(right, 1)

    # ── owner list ───────────────────────────────────────────────────────

    def _refresh_owner_list(self) -> None:
        self._owner_list.clear()
        for owner_file in sorted(_OWNER_META_DIR.glob("*.json")):
            try:
                with open(owner_file, encoding="utf-8") as f:
                    data = json.load(f)
                label = data.get("owner_name_ar", owner_file.stem)
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, owner_file.stem)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self._owner_list.addItem(item)
            except Exception:
                pass

    def _on_owner_selected(self, item: QListWidgetItem | None) -> None:
        if not item:
            return
        oid = item.data(Qt.UserRole)
        self._editing_id = oid
        self._load_owner_into_form(oid)
        self._del_btn.setVisible(True)

    def _load_owner_into_form(self, owner_id: str) -> None:
        meta_path = _OWNER_META_DIR / f"{owner_id}.json"
        try:
            with open(meta_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        self._form_title.setText(f"تعديل: {data.get('owner_name_ar', owner_id)}")
        self._fid.setText(data.get("owner_id", owner_id))
        self._fid.setEnabled(False)   # لا يمكن تغيير المعرّف
        self._far.setText(data.get("owner_name_ar", ""))
        self._fen.setText(data.get("owner_name_en", ""))
        self._fcode.setText(data.get("owner_code", ""))
        self._fcontact.setText(data.get("contact", ""))

        nets = data.get("applicable_networks", [])
        for nid, cb in self._net_checks.items():
            cb.setChecked(nid in nets)

        cfg_spec = self._config_data.get("owner_specifications", {}).get(owner_id, {})
        self._mandatory_codes = list(cfg_spec.get("mandatory_codes", []))
        self._mand_btn.setText(f"🔒  الأكواد الإلزامية ({len(self._mandatory_codes)})")

    def _new_owner(self) -> None:
        self._editing_id = None
        self._form_title.setText("إضافة جهة مالكة جديدة")
        self._fid.setEnabled(True)
        for w in [self._fid, self._far, self._fen, self._fcode, self._fcontact]:
            w.clear()
        for cb in self._net_checks.values():
            cb.setChecked(False)
        self._mandatory_codes = []
        self._mand_btn.setText("🔒  الأكواد الإلزامية (0)")
        self._del_btn.setVisible(False)
        self._owner_list.clearSelection()

    # ── mandatory codes picker ───────────────────────────────────────────

    def _pick_mandatory(self) -> None:
        all_codes = self._registry_data.get("codes", {})
        options = [
            (cid, f"{cid} — {cd.get('activity_name_ar', cid)}")
            for cid, cd in sorted(all_codes.items())
            if cd.get("status") == "active"
        ]
        dlg = _MultiSelectDialog(
            "اختر الأكواد الإلزامية", options, self._mandatory_codes, self
        )
        if dlg.exec_() == QDialog.Accepted:
            self._mandatory_codes = dlg.selected_ids()
            self._mand_btn.setText(f"🔒  الأكواد الإلزامية ({len(self._mandatory_codes)})")

    # ── save / delete ────────────────────────────────────────────────────

    def _do_save_owner(self) -> None:
        oid  = self._fid.text().strip().lower().replace(" ", "_")
        ar   = self._far.text().strip()
        en   = self._fen.text().strip()
        code = self._fcode.text().strip().upper()

        if not oid:
            QMessageBox.warning(self, "تنبيه", "المعرّف (ID) مطلوب.")
            return
        if not ar:
            QMessageBox.warning(self, "تنبيه", "الاسم العربي مطلوب.")
            return

        is_new = (self._editing_id is None)
        if is_new:
            meta_path = _OWNER_META_DIR / f"{oid}.json"
            if meta_path.exists():
                QMessageBox.warning(self, "تنبيه", f"الجهة [{oid}] موجودة بالفعل.")
                return

        nets = [nid for nid, cb in self._net_checks.items() if cb.isChecked()]
        today = date.today().isoformat()

        # ── حفظ metadata/owner_specifications/{oid}.json ─────────────────
        meta: dict[str, Any] = {
            "owner_id":            oid,
            "owner_name_ar":       ar,
            "owner_name_en":       en,
            "owner_code":          code or oid.upper()[:6],
            "applicable_networks": nets,
            "default_language":    "ar",
            "mandatory_codes":     self._mandatory_codes,
            "forbidden_codes":     [],
            "mandatory_sections":  ["safety", "quality_control"],
            "specific_requirements": {
                "requires_compliance_matrix": False,
                "requires_heritage_clause":   False,
                "requires_detailed_reporting":False,
                "requires_audit_trail":       True,
                "requires_as_built_drawings": True,
            },
            "style_guide": f"templates/style_templates/{oid}_style.json",
            "contact":      self._fcontact.text().strip(),
            "created_date": today,
            "last_modified": today,
            "version": "1.0",
        }
        _OWNER_META_DIR.mkdir(parents=True, exist_ok=True)
        with open(_OWNER_META_DIR / f"{oid}.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # ── حفظ في master_config.json → owner_specifications ─────────────
        owner_specs = self._config_data.setdefault("owner_specifications", {})
        owner_specs[oid] = {
            "owner_id":         oid,
            "mandatory_codes":  self._mandatory_codes,
            "forbidden_codes":  [],
            "specific_requirements": meta["specific_requirements"],
        }
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config_data, f, ensure_ascii=False, indent=2)

        # ── إنشاء ملف نمط أساسي إذا لم يكن موجوداً ──────────────────────
        style_path = _STYLE_TMPL_DIR / f"{oid}_style.json"
        if not style_path.exists():
            _STYLE_TMPL_DIR.mkdir(parents=True, exist_ok=True)
            default_style = {
                "style_id": oid,
                "owner":    en or ar,
                "scheme":   "default",
                "fonts": {
                    "body":     {"family": "Times New Roman", "size": 12, "bold": False},
                    "heading1": {"family": "Times New Roman", "size": 16, "bold": True},
                    "heading2": {"family": "Times New Roman", "size": 14, "bold": True},
                },
                "colors": {
                    "primary": "#003D7A", "secondary": "#FFFFFF",
                    "accent":  "#0066CC", "text": "#000000",
                },
                "margins_cm": {"top": 2.5, "bottom": 2.5, "left": 3.0, "right": 2.5},
            }
            with open(style_path, "w", encoding="utf-8") as f:
                json.dump(default_style, f, ensure_ascii=False, indent=2)

        verb = "إضافة" if is_new else "تحديث"
        QMessageBox.information(self, "تم", f"✅ تم {verb} الجهة [{ar}] بنجاح.")
        self._refresh_owner_list()
        self.owner_saved.emit()

    def _do_delete_owner(self) -> None:
        oid = self._editing_id
        if not oid:
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف الجهة [{oid}]؟\nلن يُحذف ملف النمط تلقائياً.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        meta_path = _OWNER_META_DIR / f"{oid}.json"
        if meta_path.exists():
            meta_path.unlink()

        owner_specs = self._config_data.get("owner_specifications", {})
        owner_specs.pop(oid, None)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config_data, f, ensure_ascii=False, indent=2)

        self._new_owner()
        self._refresh_owner_list()
        self.owner_saved.emit()
        QMessageBox.information(self, "تم", f"تم حذف الجهة [{oid}].")


# ─────────────────────────────────────────────────────────────────────────────
# النافذة الرئيسية للمعالج
# ─────────────────────────────────────────────────────────────────────────────

class ImportWizardDialog(QDialog):
    """BKL-012: نافذة المعالج الرئيسية — تبويبان: الأكواد + الجهات."""

    # يُطلق بعد أي تغيير يستوجب إعادة تحميل البيانات في MainWindow
    data_changed = pyqtSignal()

    def __init__(
        self,
        registry_data: dict,
        config_data: dict,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("📥  معالج الاستيراد وإدارة البيانات")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(820, 580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── عنوان علوي ──────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: #152433; border-bottom: 3px solid #C9921B; }"
        )
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 10, 16, 10)
        title_lbl = QLabel("📥  معالج الاستيراد وإدارة البيانات")
        title_lbl.setStyleSheet(
            "color: #C9921B; font-size: 15px; font-weight: 800; background: transparent;"
        )
        title_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addStretch()
        hl.addWidget(title_lbl)
        layout.addWidget(header)

        # ── QTabWidget ──────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.RightToLeft)
        tabs.setDocumentMode(True)
        tabs.setStyleSheet("""
            QTabWidget::pane  { border: none; background: #F8F5EE; }
            QTabBar::tab {
                background: #E8E4DC; color: #3A4A5A;
                padding: 8px 18px; font-size: 12px; font-weight: 600;
                border: 1px solid #C8C0B0; border-bottom: none;
                border-radius: 6px 6px 0 0; margin-left: 2px;
            }
            QTabBar::tab:selected {
                background: #F8F5EE; color: #152433;
                border-bottom: 2px solid #F8F5EE;
            }
            QTabBar::tab:hover:!selected { background: #DDD8CC; }
        """)

        self._codes_tab = _ImportCodesTab(registry_data, config_data)
        self._owners_tab = _OwnersTab(config_data, registry_data)

        self._codes_tab.codes_imported.connect(lambda _: self.data_changed.emit())
        self._owners_tab.owner_saved.connect(self.data_changed.emit)

        tabs.addTab(self._codes_tab,  "📥  استيراد أكواد")
        tabs.addTab(self._owners_tab, "🏢  إدارة الجهات")
        layout.addWidget(tabs, 1)

        # ── زر الإغلاق ──────────────────────────────────────────────────
        foot = QFrame()
        foot.setStyleSheet("QFrame { background: #F0EDE6; border-top: 1px solid #DDD8CC; }")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(12, 8, 12, 8)
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(_BTN_SECONDARY)
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.accept)
        fl.addStretch()
        fl.addWidget(close_btn)
        layout.addWidget(foot)


# ─────────────────────────────────────────────────────────────────────────────
# دوال مساعدة
# ─────────────────────────────────────────────────────────────────────────────

def _read_doc_title(path: Path) -> str:
    """استخرج عنوان الوثيقة من أول عنوان أو خاصية core_properties."""
    try:
        from docx import Document
        doc = Document(str(path))
        # أولاً: خصائص الوثيقة
        if doc.core_properties.title and doc.core_properties.title.strip():
            return doc.core_properties.title.strip()
        # ثانياً: أول عنوان (Heading)
        for para in doc.paragraphs:
            if para.style.name.startswith("Heading") and para.text.strip():
                return para.text.strip()[:80]
        # ثالثاً: أول فقرة غير فارغة
        for para in doc.paragraphs:
            if para.text.strip():
                return para.text.strip()[:80]
    except Exception:
        pass
    return ""


def _estimate_pages(path: Path | None) -> int:
    """تقدير عدد الصفحات من عدد الكلمات (~400 كلمة/صفحة)."""
    if not path or not path.exists():
        return 0
    try:
        from docx import Document
        doc = Document(str(path))
        words = sum(len(p.text.split()) for p in doc.paragraphs)
        return max(1, words // 400)
    except Exception:
        return 0
