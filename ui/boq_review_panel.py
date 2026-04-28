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
from utils.json_manager import load_json


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

    _COL_ITEM = 0
    _COL_CODE = 1
    _COL_SCORE = 2
    _COL_STATUS = 3

    _COLOR_OK = QColor("#d4edda")
    _COLOR_WARN = QColor("#fff3cd")
    _COLOR_NEW = QColor("#cce5ff")

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

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self._file_label = QLabel("لم يُختر ملف بعد")
        btn_open = QPushButton("اختر ملف Excel...")
        btn_open.clicked.connect(self._on_open_file)
        top.addWidget(btn_open)
        top.addWidget(self._file_label, 1)
        layout.addLayout(top)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["البند", "الكود المقترح", "التطابق %", "الحالة"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.cellDoubleClicked.connect(self._on_cell_double_click)
        layout.addWidget(self._table)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("موافق — ابنِ العرض")
        buttons.button(QDialogButtonBox.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
                self._table.setItem(row, self._COL_CODE, QTableWidgetItem("⚠️ غير موجود — اضغط لإضافة"))
                self._table.setItem(row, self._COL_SCORE, QTableWidgetItem(f"{r.score:.0%}"))
                self._table.setItem(row, self._COL_STATUS, QTableWidgetItem("غير موجود"))
                color = self._COLOR_WARN

            for col in range(4):
                item = self._table.item(row, col)
                if item:
                    item.setBackground(color)

    def _on_cell_double_click(self, row: int, col: int) -> None:
        if row >= len(self._results):
            return
        result = self._results[row]
        if result.code_id is not None:
            return

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

    def get_selected_codes(self) -> list[str]:
        """يُرجع قائمة code_ids الموافق عليها."""
        return [r.code_id for r in self._results if r.code_id]
