#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BKL-010: تقرير ما بعد البناء (Post-Build Report Dialog).

يُعرض تلقائياً عند نجاح بناء العرض الفني.
يُظهر ملخصاً شاملاً: اسم الملف، عدد الأكواد، الصفحات، الحجم، الوقت المستغرق.
أزرار: فتح الملف | فتح المجلد | بناء عرض جديد | إغلاق.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from ui import theme


# ─────────────────────────────────────────────────────────────────────────────
# بطاقة إحصاء واحدة
# ─────────────────────────────────────────────────────────────────────────────

def _stat_card(icon: str, label: str, value: str, color: str, parent: QWidget) -> QWidget:
    """بطاقة صغيرة تُظهر أيقونة + تسمية + قيمة."""
    card = QWidget(parent)
    card.setStyleSheet(f"""
        QWidget {{
            background: white;
            border: 1px solid #E0E0E0;
            border-top: 4px solid {color};
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(4)

    icon_lbl = QLabel(icon, card)
    icon_lbl.setAlignment(Qt.AlignCenter)
    icon_lbl.setStyleSheet(
        "font-size: 22px; background: transparent; border: none;"
    )

    val_lbl = QLabel(value, card)
    val_lbl.setAlignment(Qt.AlignCenter)
    val_lbl.setStyleSheet(
        f"font-size: 18px; font-weight: 900; color: {color}; "
        "background: transparent; border: none;"
    )

    lbl_lbl = QLabel(label, card)
    lbl_lbl.setAlignment(Qt.AlignCenter)
    lbl_lbl.setStyleSheet(
        "font-size: 10px; color: #666; background: transparent; border: none;"
    )
    lbl_lbl.setWordWrap(True)

    layout.addWidget(icon_lbl)
    layout.addWidget(val_lbl)
    layout.addWidget(lbl_lbl)

    return card


# ─────────────────────────────────────────────────────────────────────────────
# BuildReportDialog
# ─────────────────────────────────────────────────────────────────────────────

class BuildReportDialog(QDialog):
    """
    تقرير ما بعد البناء — يُعرض تلقائياً عند نجاح BuildProgressDialog.

    Parameters
    ----------
    output_path : Path
        مسار ملف Word الناتج.
    selected_codes : list[str]
        الأكواد التي بُني منها العرض.
    registry_codes : dict
        قاموس الأكواد من codes_registry.json (لحساب عدد الصفحات).
    elapsed_seconds : float
        الوقت المستغرق في البناء.
    parent : QWidget | None
    """

    # يُطلق عند الضغط على «بناء عرض جديد»
    new_build_requested = __import__("PyQt5.QtCore", fromlist=["pyqtSignal"]).pyqtSignal()

    def __init__(
        self,
        output_path: Path,
        selected_codes: list[str],
        registry_codes: dict[str, Any],
        elapsed_seconds: float = 0.0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("✅ العرض الفني جاهز")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumWidth(500)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._output_path = output_path
        self._selected_codes = selected_codes
        self._registry_codes = registry_codes
        self._elapsed = elapsed_seconds

        self._build_ui()

    # ------------------------------------------------------------------
    # بناء الواجهة
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 14)

        # ── رأس النجاح ─────────────────────────────────────────────────
        header = QWidget(self)
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1B5E20, stop:1 #2E7D32);
                border-radius: 10px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 14, 16, 14)

        check_lbl = QLabel("✅", header)
        check_lbl.setStyleSheet(
            "font-size: 32px; background: transparent;"
        )

        h_text = QVBoxLayout()
        h_text.setSpacing(2)

        title_lbl = QLabel("العرض الفني جاهز للتقديم!", header)
        title_lbl.setStyleSheet(
            "color: white; font-size: 16px; font-weight: 900; background: transparent;"
        )

        fname_lbl = QLabel(self._output_path.name, header)
        fname_lbl.setStyleSheet(
            "color: #A5D6A7; font-size: 11px; background: transparent;"
        )
        fname_lbl.setWordWrap(True)

        h_text.addWidget(title_lbl)
        h_text.addWidget(fname_lbl)

        h_layout.addWidget(check_lbl)
        h_layout.addLayout(h_text, stretch=1)
        layout.addWidget(header)

        # ── بطاقات الإحصاء ──────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)

        code_count = len(self._selected_codes)
        page_count = self._estimate_pages()
        file_size  = self._file_size_kb()
        elapsed_s  = f"{self._elapsed:.1f} ث"

        stats_row.addWidget(_stat_card(
            "📋", "عدد الأكواد",
            str(code_count), "#152433", self,
        ))
        stats_row.addWidget(_stat_card(
            "📄", "الصفحات التقديرية",
            str(page_count), "#1C3045", self,
        ))
        stats_row.addWidget(_stat_card(
            "💾", "حجم الملف",
            file_size, "#2E7D32", self,
        ))
        stats_row.addWidget(_stat_card(
            "⏱️", "وقت البناء",
            elapsed_s, "#C9921B", self,
        ))
        layout.addLayout(stats_row)

        # ── مسار الملف ─────────────────────────────────────────────────
        path_lbl = QLabel(f"📂 {self._output_path.resolve()}", self)
        path_lbl.setLayoutDirection(Qt.LeftToRight)
        path_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        path_lbl.setStyleSheet(
            "font-size: 10px; color: #2D7A4F; background: #EBF7F1; "
            "border-radius: 5px; padding: 6px 10px;"
        )
        path_lbl.setWordWrap(True)
        layout.addWidget(path_lbl)

        # ── قائمة الأكواد المختصرة ──────────────────────────────────────
        if self._selected_codes:
            codes_preview = "  ·  ".join(self._selected_codes[:8])
            if len(self._selected_codes) > 8:
                codes_preview += f"  ... (+{len(self._selected_codes) - 8})"

            codes_lbl = QLabel(codes_preview, self)
            codes_lbl.setStyleSheet(
                "font-size: 10px; color: #555; background: #F5F5F5; "
                "border-radius: 5px; padding: 5px 10px;"
            )
            codes_lbl.setWordWrap(True)
            codes_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(codes_lbl)

        # ── أزرار الإجراءات ─────────────────────────────────────────────
        btn_row_1 = QHBoxLayout()
        btn_row_1.setSpacing(8)

        open_btn = QPushButton("📄  فتح الملف في Word", self)
        open_btn.setStyleSheet(self._btn_style(theme.HEADER, theme.ACCENT))
        open_btn.clicked.connect(self._open_file)
        open_btn.setCursor(Qt.PointingHandCursor)

        folder_btn = QPushButton("📁  فتح المجلد", self)
        folder_btn.setStyleSheet(self._btn_style("#1C3045", "white"))
        folder_btn.clicked.connect(self._open_folder)
        folder_btn.setCursor(Qt.PointingHandCursor)

        btn_row_1.addWidget(open_btn, stretch=2)
        btn_row_1.addWidget(folder_btn, stretch=1)
        layout.addLayout(btn_row_1)

        btn_row_2 = QHBoxLayout()
        btn_row_2.setSpacing(8)

        new_btn = QPushButton("🔄  بناء عرض جديد", self)
        new_btn.setStyleSheet(self._btn_style(theme.WARNING, "white"))
        new_btn.clicked.connect(self._on_new_build)
        new_btn.setCursor(Qt.PointingHandCursor)

        close_btn = QPushButton("إغلاق", self)
        close_btn.setStyleSheet("""
            QPushButton {
                color: #666; background: white; border: 1px solid #CCC;
                border-radius: 6px; padding: 8px 20px; font-size: 12px;
            }
            QPushButton:hover { background: #F5F5F5; }
        """)
        close_btn.clicked.connect(self.accept)
        close_btn.setCursor(Qt.PointingHandCursor)

        btn_row_2.addWidget(new_btn, stretch=2)
        btn_row_2.addWidget(close_btn, stretch=1)
        layout.addLayout(btn_row_2)

    # ------------------------------------------------------------------
    # مساعدات
    # ------------------------------------------------------------------

    @staticmethod
    def _btn_style(bg: str, fg: str) -> str:
        return f"""
            QPushButton {{
                background: {bg}; color: {fg};
                border: none; border-radius: 6px;
                padding: 9px 16px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """

    def _estimate_pages(self) -> int:
        total = 0
        for code_id in self._selected_codes:
            code = self._registry_codes.get(code_id, {})
            total += max(1, int(code.get("page_count", 1)))
        return total

    def _file_size_kb(self) -> str:
        try:
            size = self._output_path.stat().st_size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size // 1024} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except OSError:
            return "—"

    # ------------------------------------------------------------------
    # مداخل الأزرار
    # ------------------------------------------------------------------

    def _open_file(self) -> None:
        path = self._output_path.resolve()
        if not path.exists():
            QMessageBox.warning(
                self,
                "الملف غير موجود",
                f"لم أجد ملف العرض الفني في المسار:\n{path}",
            )
            return
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(
                self,
                "تعذّر فتح الملف",
                f"تم إنشاء العرض، لكن تعذّر فتحه تلقائياً:\n{exc}",
            )

    def _open_folder(self) -> None:
        path = self._output_path.resolve()
        folder = path.parent
        if not folder.exists():
            QMessageBox.warning(
                self,
                "المجلد غير موجود",
                f"لم أجد مجلد المخرجات:\n{folder}",
            )
            return
        try:
            if sys.platform == "win32":
                # explorer.exe always exits with code 1 — use Popen to avoid false error.
                if path.exists():
                    subprocess.Popen(["explorer", f"/select,{path}"])
                else:
                    subprocess.Popen(["explorer", str(folder)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(
                self,
                "تعذّر فتح المجلد",
                f"تم إنشاء العرض، لكن تعذّر فتح مجلد المخرجات:\n{exc}",
            )

    def _on_new_build(self) -> None:
        self.new_build_requested.emit()
        self.accept()
