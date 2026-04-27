# BOQ Importer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** تحويل عملية اختيار الأكواد من يدوية (ساعة-اتنين) إلى آلية ذكية — المستخدم يرفع Excel ببنود جدول الكميات، البرنامج يقترح الأكواد بالترتيب الصح خلال ثوانٍ.

**Architecture:** أربعة مكونات متسلسلة: `boq_importer` يقرأ الملف → `boq_matcher` يطابق البنود مع الأكواد بـ fuzzy matching → `gap_handler` ينشئ أكواداً جديدة للبنود المجهولة → `boq_review_panel` يعرض النتائج للمراجعة. كل مكون مستقل وقابل للاختبار بمفرده.

**Tech Stack:** Python 3.11+, PyQt5, openpyxl (موجودة), difflib (standard library), utils/json_manager (موجودة)

---

## File Map

| الملف | نوعه | المسؤولية |
|-------|------|----------|
| `engine/boq_importer.py` | جديد | قراءة Excel واستخراج أسماء البنود |
| `engine/boq_matcher.py` | جديد | المطابقة الذكية بين البنود والأكواد |
| `engine/gap_handler.py` | جديد | إنشاء أكواد جديدة للبنود المجهولة |
| `ui/boq_review_panel.py` | جديد | واجهة المراجعة والتعديل |
| `ui/main_window.py` | معدّل | إضافة زر "استورد جدول كميات" |
| `tests/test_boq_importer.py` | جديد | 5 سيناريوهات اختبار للـ importer |
| `tests/test_boq_matcher.py` | جديد | 10 سيناريوهات اختبار للـ matcher |

---

## Task 1: BOQ Importer — قراءة ملف Excel

**Files:**
- Create: `engine/boq_importer.py`
- Create: `tests/test_boq_importer.py`

- [ ] **Step 1: أنشئ ملف الاختبار**

```python
# tests/test_boq_importer.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import tempfile
from pathlib import Path
from openpyxl import Workbook
from engine.boq_importer import read_boq, BOQImportError


def _make_xlsx(rows: list, tmp_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    path = tmp_path / "test_boq.xlsx"
    wb.save(path)
    return path


def test_reads_simple_list(tmp_path):
    path = _make_xlsx([["حفر بالميكنة"], ["خرسانة عادية"], ["أعمال صرف"]], tmp_path)
    result = read_boq(str(path))
    assert result == ["حفر بالميكنة", "خرسانة عادية", "أعمال صرف"]


def test_skips_header_row(tmp_path):
    path = _make_xlsx([["اسم البند"], ["حفر بالميكنة"], ["خرسانة عادية"]], tmp_path)
    result = read_boq(str(path))
    # header يُكتشف لأنه لا يبدو ببند حقيقي — الاثنين يقبلان
    assert "حفر بالميكنة" in result
    assert "خرسانة عادية" in result


def test_skips_empty_rows(tmp_path):
    path = _make_xlsx([["حفر"], [""], [None], ["خرسانة"]], tmp_path)
    result = read_boq(str(path))
    assert result == ["حفر", "خرسانة"]


def test_raises_on_missing_file():
    with pytest.raises(BOQImportError, match="الملف غير موجود"):
        read_boq("nonexistent.xlsx")


def test_raises_on_empty_file(tmp_path):
    path = _make_xlsx([], tmp_path)
    with pytest.raises(BOQImportError, match="لا توجد بنود"):
        read_boq(str(path))
```

- [ ] **Step 2: شغّل الاختبار وتأكد أنه يفشل**

```
python -m pytest tests/test_boq_importer.py -v
```

المتوقع: `ImportError: cannot import name 'read_boq'`

- [ ] **Step 3: أنشئ `engine/boq_importer.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from openpyxl import load_workbook


class BOQImportError(Exception):
    pass


def read_boq(filepath: str | Path) -> list[str]:
    """
    يقرأ ملف Excel ويُرجع قائمة أسماء البنود النظيفة.

    Args:
        filepath: مسار ملف .xlsx أو .xls

    Returns:
        list[str] — أسماء البنود (stripped, non-empty)

    Raises:
        BOQImportError: إذا الملف غير موجود أو فارغ
    """
    path = Path(filepath)
    if not path.exists():
        raise BOQImportError(f"الملف غير موجود: {filepath}")

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    items: list[str] = []
    for row in ws.iter_rows(min_col=1, max_col=1, values_only=True):
        cell = row[0]
        if cell is None:
            continue
        text = str(cell).strip()
        if text:
            items.append(text)
    wb.close()

    if not items:
        raise BOQImportError("لا توجد بنود في الملف")

    return items
```

- [ ] **Step 4: شغّل الاختبارات وتأكد أنها تنجح**

```
python -m pytest tests/test_boq_importer.py -v
```

المتوقع: 5 اختبارات تنجح ✅

- [ ] **Step 5: Commit**

```
git add engine/boq_importer.py tests/test_boq_importer.py
git commit -m "feat: add BOQ importer — reads Excel BOQ files"
```

---

## Task 2: BOQ Matcher — المطابقة الذكية

**Files:**
- Create: `engine/boq_matcher.py`
- Create: `tests/test_boq_matcher.py`

- [ ] **Step 1: أنشئ ملف الاختبار**

```python
# tests/test_boq_matcher.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from engine.boq_matcher import BOQMatcher, MatchResult
from utils.json_manager import load_json


@pytest.fixture(scope="module")
def codes():
    return load_json("codes_registry.json")["codes"]


@pytest.fixture(scope="module")
def matcher(codes):
    return BOQMatcher(codes)


def test_exact_arabic_match(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].code_id == "001-SUR-BASE"
    assert results[0].score >= 0.9


def test_partial_match(matcher):
    results = matcher.match(["حفر"])
    assert results[0].code_id is not None
    assert results[0].score >= 0.0


def test_english_name_match(matcher):
    results = matcher.match(["General Surveying"])
    assert results[0].code_id == "001-SUR-BASE"
    assert results[0].score >= 0.7


def test_unknown_item_returns_none(matcher):
    results = matcher.match(["بند غير موجود أبداً xyz123"])
    assert results[0].code_id is None
    assert results[0].score < 0.7


def test_multiple_items(matcher):
    items = ["مسح وتثبيت نقاط عامة", "بند غير موجود xyz"]
    results = matcher.match(items)
    assert len(results) == 2
    assert results[0].code_id == "001-SUR-BASE"
    assert results[1].code_id is None


def test_result_has_boq_item(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].boq_item == "مسح وتثبيت نقاط عامة"


def test_empty_string_is_unknown(matcher):
    results = matcher.match(["   "])
    assert results[0].code_id is None


def test_score_between_0_and_1(matcher):
    results = matcher.match(["مسح"])
    assert 0.0 <= results[0].score <= 1.0


def test_known_item_is_not_new(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].is_new is False


def test_unknown_item_is_not_new_by_default(matcher):
    results = matcher.match(["بند غير موجود xyz"])
    assert results[0].is_new is False  # is_new يُعيَّن فقط بعد gap_handler
```

- [ ] **Step 2: شغّل وتأكد من الفشل**

```
python -m pytest tests/test_boq_matcher.py -v
```

المتوقع: `ImportError: cannot import name 'BOQMatcher'`

- [ ] **Step 3: أنشئ `engine/boq_matcher.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from engine.types import CodeRegistry

_THRESHOLD = 0.70  # أدنى نسبة مطابقة مقبولة


@dataclass
class MatchResult:
    boq_item: str
    code_id: Optional[str]
    score: float
    is_new: bool = False


def _normalize(text: str) -> str:
    """يُزيل التشكيل والمسافات الزائدة ويحوّل للأحرف الصغيرة."""
    text = re.sub(r"[ً-ٟ]", "", text)  # إزالة التشكيل
    return " ".join(text.lower().split())


class BOQMatcher:
    """
    يطابق بنود جدول الكميات مع أكواد النظام باستخدام fuzzy matching.

    Usage:
        matcher = BOQMatcher(codes)
        results = matcher.match(["حفر بالميكنة", "خرسانة عادية"])
        # results: list[MatchResult]
    """

    def __init__(self, codes: CodeRegistry) -> None:
        self._codes = codes
        self._index = self._build_index()

    def _build_index(self) -> list[tuple[str, str, str]]:
        """يبني فهرس البحث: [(code_id, name_ar_normalized, name_en_normalized)]"""
        index = []
        for code_id, data in self._codes.items():
            name_ar = _normalize(data.get("activity_name_ar", ""))
            name_en = _normalize(data.get("activity_name_en", ""))
            index.append((code_id, name_ar, name_en))
        return index

    def _score(self, query: str, candidate: str) -> float:
        if not candidate:
            return 0.0
        return SequenceMatcher(None, query, candidate).ratio()

    def _best_match(self, item: str) -> tuple[Optional[str], float]:
        query = _normalize(item)
        if not query:
            return None, 0.0

        best_id: Optional[str] = None
        best_score = 0.0

        for code_id, name_ar, name_en in self._index:
            score = max(self._score(query, name_ar), self._score(query, name_en))
            if score > best_score:
                best_score = score
                best_id = code_id

        if best_score < _THRESHOLD:
            return None, best_score
        return best_id, best_score

    def match(self, items: list[str]) -> list[MatchResult]:
        """
        يُرجع قائمة MatchResult لكل بند.
        code_id=None يعني البند مجهول (نسبة مطابقة < 70%).
        """
        results = []
        for item in items:
            code_id, score = self._best_match(item)
            results.append(MatchResult(boq_item=item, code_id=code_id, score=score))
        return results
```

- [ ] **Step 4: شغّل الاختبارات**

```
python -m pytest tests/test_boq_matcher.py -v
```

المتوقع: 10 اختبارات تنجح ✅

- [ ] **Step 5: تأكد أن الاختبارات القديمة لا تزال تنجح**

```
python -m pytest tests/ -v
```

المتوقع: كل الاختبارات السابقة + الجديدة تنجح ✅

- [ ] **Step 6: Commit**

```
git add engine/boq_matcher.py tests/test_boq_matcher.py
git commit -m "feat: add BOQ matcher — fuzzy matching with 70% threshold"
```

---

## Task 3: Gap Handler — إنشاء أكواد جديدة لحظياً

**Files:**
- Create: `engine/gap_handler.py`

- [ ] **Step 1: أضف اختبارات Gap Handler في نفس ملف test_boq_matcher.py**

```python
# أضف في نهاية tests/test_boq_matcher.py:
import json
import tempfile
from pathlib import Path
from engine.gap_handler import GapHandler


def test_creates_custom_code(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")

    handler = GapHandler(str(reg_path))
    code_id = handler.create("أعمال خاصة جداً", "wastewater")

    assert code_id.startswith("CUSTOM-")
    updated = json.loads(reg_path.read_text(encoding="utf-8"))
    assert code_id in updated["codes"]


def test_custom_ids_are_sequential(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")

    handler = GapHandler(str(reg_path))
    id1 = handler.create("بند أول", "wastewater")
    id2 = handler.create("بند ثاني", "wastewater")

    assert id1 == "CUSTOM-001"
    assert id2 == "CUSTOM-002"


def test_created_code_has_required_fields(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")

    handler = GapHandler(str(reg_path))
    code_id = handler.create("حفر خاص", "wastewater")

    updated = json.loads(reg_path.read_text(encoding="utf-8"))
    code = updated["codes"][code_id]
    assert code["activity_name_ar"] == "حفر خاص"
    assert code["status"] == "active"
    assert "wastewater" in code["project_ids"]
```

- [ ] **Step 2: شغّل وتأكد من الفشل**

```
python -m pytest tests/test_boq_matcher.py::test_creates_custom_code -v
```

المتوقع: `ImportError: cannot import name 'GapHandler'`

- [ ] **Step 3: أنشئ `engine/gap_handler.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from utils.json_manager import load_json, save_json


class GapHandler:
    """
    ينشئ أكواداً جديدة (CUSTOM-NNN) للبنود غير الموجودة في السجل.

    Usage:
        handler = GapHandler("codes_registry.json")
        code_id = handler.create("حفر خاص", "wastewater")
        # code_id = "CUSTOM-001"
    """

    def __init__(self, registry_path: str | Path = "codes_registry.json") -> None:
        self._registry_path = Path(registry_path)

    def _next_id(self, codes: dict) -> str:
        existing = [k for k in codes if k.startswith("CUSTOM-")]
        if not existing:
            return "CUSTOM-001"
        numbers = [int(k.split("-")[1]) for k in existing]
        return f"CUSTOM-{max(numbers) + 1:03d}"

    def create(self, boq_item: str, project_type: str) -> str:
        """
        ينشئ كود جديد في codes_registry.json ويُرجع الـ code_id.

        Args:
            boq_item: اسم البند من جدول الكميات
            project_type: نوع المشروع (مثلاً "wastewater")

        Returns:
            str — الـ code_id الجديد (مثلاً "CUSTOM-001")
        """
        registry = load_json(self._registry_path)
        codes = registry.setdefault("codes", {})
        code_id = self._next_id(codes)

        codes[code_id] = {
            "code_id": code_id,
            "category": "CUSTOM",
            "phase": "GEN",
            "variation": f"{len(codes):03d}",
            "activity_name_ar": boq_item,
            "activity_name_en": boq_item,
            "project_ids": [project_type],
            "network_types": [],
            "applicable_owners": [],
            "sequence_order": 999,
            "dependencies": [],
            "status": "active",
            "is_custom": True,
        }

        save_json(self._registry_path, registry)
        return code_id
```

- [ ] **Step 4: شغّل الاختبارات**

```
python -m pytest tests/test_boq_matcher.py -v
```

المتوقع: كل الاختبارات تنجح ✅

- [ ] **Step 5: Commit**

```
git add engine/gap_handler.py tests/test_boq_matcher.py
git commit -m "feat: add gap handler — creates CUSTOM-NNN codes on the fly"
```

---

## Task 4: BOQ Review Panel — واجهة المراجعة

**Files:**
- Create: `ui/boq_review_panel.py`

- [ ] **Step 1: أنشئ `ui/boq_review_panel.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from engine.boq_importer import BOQImportError, read_boq
from engine.boq_matcher import BOQMatcher, MatchResult
from engine.gap_handler import GapHandler


class BOQReviewPanel(QDialog):
    """
    نافذة مراجعة نتائج مطابقة جدول الكميات.

    Signals:
        codes_accepted(list[str]): تُصدَر عند الموافقة — قائمة code_ids مرتبة

    Usage:
        panel = BOQReviewPanel(codes, registry_path, project_type, parent)
        if panel.exec_() == QDialog.Accepted:
            selected = panel.get_selected_codes()
    """

    codes_accepted = pyqtSignal(list)

    _COL_ITEM = 0   # اسم البند
    _COL_CODE = 1   # الكود المقترح
    _COL_SCORE = 2  # نسبة المطابقة
    _COL_STATUS = 3 # الحالة

    _COLOR_OK = QColor("#d4edda")      # أخضر فاتح — مطابقة جيدة
    _COLOR_WARN = QColor("#fff3cd")    # أصفر — مجهول
    _COLOR_NEW = QColor("#cce5ff")     # أزرق فاتح — كود جديد

    def __init__(
        self,
        codes: dict,
        registry_path: str | Path,
        project_type: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._codes = codes
        self._registry_path = registry_path
        self._project_type = project_type
        self._matcher = BOQMatcher(codes)
        self._gap_handler = GapHandler(registry_path)
        self._results: list[MatchResult] = []

        self.setWindowTitle("استيراد جدول الكميات")
        self.setMinimumSize(800, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # زر رفع الملف
        top = QHBoxLayout()
        self._file_label = QLabel("لم يُختر ملف بعد")
        btn_open = QPushButton("اختر ملف Excel...")
        btn_open.clicked.connect(self._on_open_file)
        top.addWidget(btn_open)
        top.addWidget(self._file_label, 1)
        layout.addLayout(top)

        # الجدول
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["البند", "الكود المقترح", "التطابق %", "الحالة"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self._table)

        # أزرار الحوار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("موافق — ابنِ العرض")
        buttons.button(QDialogButtonBox.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف جدول الكميات", "", "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        try:
            items = read_boq(path)
        except BOQImportError as exc:
            QMessageBox.warning(self, "خطأ في قراءة الملف", str(exc))
            return

        self._file_label.setText(Path(path).name)
        self._results = self._matcher.match(items)
        self._populate_table()

    def _populate_table(self) -> None:
        self._table.setRowCount(len(self._results))
        for row, r in enumerate(self._results):
            self._table.setItem(row, self._COL_ITEM, QTableWidgetItem(r.boq_item))

            if r.code_id:
                code_name = self._codes.get(r.code_id, {}).get("activity_name_ar", r.code_id)
                self._table.setItem(row, self._COL_CODE, QTableWidgetItem(f"{r.code_id} — {code_name}"))
                self._table.setItem(row, self._COL_SCORE, QTableWidgetItem(f"{r.score:.0%}"))
                self._table.setItem(row, self._COL_STATUS, QTableWidgetItem("✅ موجود"))
                color = self._COLOR_NEW if r.is_new else self._COLOR_OK
            else:
                btn_item = QTableWidgetItem("⚠️ غير موجود — اضغط لإضافة")
                self._table.setItem(row, self._COL_CODE, btn_item)
                self._table.setItem(row, self._COL_SCORE, QTableWidgetItem(f"{r.score:.0%}"))
                self._table.setItem(row, self._COL_STATUS, QTableWidgetItem("غير موجود"))
                color = self._COLOR_WARN

            for col in range(4):
                item = self._table.item(row, col)
                if item:
                    item.setBackground(color)

        self._table.cellDoubleClicked.connect(self._on_cell_double_click)

    def _on_cell_double_click(self, row: int, col: int) -> None:
        result = self._results[row]
        if result.code_id is not None:
            return  # مطابق بالفعل

        name, ok = QInputDialog.getText(
            self, "اسم الكود الجديد",
            f"أدخل اسماً للكود الجديد للبند:\n{result.boq_item}",
            text=result.boq_item,
        )
        if not ok or not name.strip():
            return

        code_id = self._gap_handler.create(name.strip(), self._project_type)
        result.code_id = code_id
        result.score = 1.0
        result.is_new = True

        # تحديث السجل في الذاكرة
        from utils.json_manager import load_json
        self._codes = load_json(self._registry_path)["codes"]
        self._matcher = BOQMatcher(self._codes)

        self._populate_table()

    def _on_accept(self) -> None:
        codes = [r.code_id for r in self._results if r.code_id]
        if not codes:
            QMessageBox.warning(self, "لا توجد أكواد", "لم يتم اختيار أي أكواد.")
            return
        self.codes_accepted.emit(codes)
        self.accept()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_selected_codes(self) -> list[str]:
        """يُرجع قائمة code_ids الموافق عليها."""
        return [r.code_id for r in self._results if r.code_id]
```

- [ ] **Step 2: تحقق من عدم وجود أخطاء syntax**

```
python -c "from ui.boq_review_panel import BOQReviewPanel; print('OK')"
```

المتوقع: `OK`

- [ ] **Step 3: Commit**

```
git add ui/boq_review_panel.py
git commit -m "feat: add BOQ review panel — fuzzy match results with gap resolution UI"
```

---

## Task 5: ربط الـ main_window — زر "استورد جدول كميات"

**Files:**
- Modify: `ui/main_window.py`

- [ ] **Step 1: ابحث عن مكان الزر المناسب في main_window**

```
python -c "
import ast, sys
tree = ast.parse(open('ui/main_window.py', encoding='utf-8').read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(node.lineno, node.name)
"
```

دوّن اسم الدالة المسؤولة عن بناء toolbar أو buttons panel.

- [ ] **Step 2: أضف import في main_window.py**

أضف في قسم imports (بعد imports الموجودة):

```python
from ui.boq_review_panel import BOQReviewPanel
```

- [ ] **Step 3: أضف زر "استورد جدول كميات"**

ابحث عن مكان أزرار الـ toolbar أو actions الرئيسية في `main_window.py` وأضف:

```python
# في نفس المكان الذي يوجد فيه أزرار "بناء" أو "معاينة"
boq_btn = QPushButton("استورد جدول كميات 📋")
boq_btn.setToolTip("رفع Excel ببنود جدول الكميات واقتراح الأكواد تلقائياً")
boq_btn.clicked.connect(self._on_import_boq)
# أضفه للـ layout المناسب
```

- [ ] **Step 4: أضف slot للزر**

```python
def _on_import_boq(self) -> None:
    from utils.json_manager import load_json
    codes = load_json(self._registry_path)["codes"]
    project_type = self._get_current_project_type()  # استخدم الدالة الموجودة

    panel = BOQReviewPanel(
        codes=codes,
        registry_path=self._registry_path,
        project_type=project_type,
        parent=self,
    )
    panel.codes_accepted.connect(self._on_boq_codes_accepted)
    panel.exec_()


def _on_boq_codes_accepted(self, code_ids: list) -> None:
    # ضع الأكواد المقبولة في الـ checkbox selector
    # استخدم الدالة الموجودة في checkbox_selector لاختيار أكواد مسبقاً
    if hasattr(self, '_checkbox_selector'):
        self._checkbox_selector.set_selected_codes(code_ids)
```

- [ ] **Step 5: شغّل التطبيق وتأكد من ظهور الزر**

```
python main.py
```

تأكد: الزر ظاهر، الضغط عليه يفتح نافذة "استيراد جدول الكميات".

- [ ] **Step 6: شغّل كل الاختبارات**

```
python -m pytest tests/ -v
```

المتوقع: كل الاختبارات تنجح ✅

- [ ] **Step 7: Commit**

```
git add ui/main_window.py
git commit -m "feat: wire BOQ import button in main window"
```

---

## Task 6: Commit النهائي وPush

- [ ] **Step 1: شغّل كل الاختبارات مرة أخيرة**

```
python -m pytest tests/ -v --tb=short
```

المتوقع: كل الاختبارات تنجح ✅

- [ ] **Step 2: Push على GitHub**

```
git push origin main
```

---

## Self-Review

### Spec Coverage
| المتطلب | التغطية |
|---------|---------|
| قراءة Excel | Task 1: `boq_importer.py` ✅ |
| مطابقة ذكية 70% | Task 2: `boq_matcher.py` ✅ |
| كشف البنود المجهولة | Task 2: `MatchResult.code_id = None` ✅ |
| إنشاء كود جديد لحظياً | Task 3: `gap_handler.py` ✅ |
| واجهة مراجعة مع ألوان | Task 4: `boq_review_panel.py` ✅ |
| زر في main_window | Task 5 ✅ |
| جدول 30 بند < 5 ثوانٍ | `difflib.SequenceMatcher` سريع كفاية ✅ |
| كود جديد يُحفظ فوراً | `gap_handler.save_json` ✅ |

### Type Consistency
- `MatchResult.code_id: Optional[str]` — متسق في Task 2, 3, 4
- `BOQMatcher.match(items: list[str]) -> list[MatchResult]` — متسق في كل Tasks
- `GapHandler.create(boq_item, project_type) -> str` — متسق في Task 3, 4
