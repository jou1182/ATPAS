#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ATPAS License Key Generator
============================
أداة توليد أكواد الترخيص — للمطوّر فقط
تُوزَّع EXE مشفَّراً، لا تُرسَل للعملاء
"""

import csv
import hashlib
import hmac
import json
import os
import sys
import uuid
import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PyQt5.QtCore import (
    Qt, QDate, QPropertyAnimation, QRect, QTimer,
)
from PyQt5.QtGui import (
    QColor, QFont, QFontDatabase, QIcon, QPalette,
)
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QDialog, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

# ═══════════════════════════════════════════════════════════════════════════
# HMAC Secret — same bytes as license_manager.py
# مقسَّم لمنع الاكتشاف السهل في الذاكرة
# ═══════════════════════════════════════════════════════════════════════════
_P1 = b"\x52\x61\x77\x61\x66"      # Rawaf
_P2 = b"\x2d\x41\x54\x50\x41\x53"  # -ATPAS
_P3 = b"\x2d\x4c\x49\x43\x2d"      # -LIC-
_P4 = b"\x32\x30\x32\x34\x58\x39"  # 2024X9
_HMAC_KEY: bytes = _P1 + _P2 + _P3 + _P4

_EPOCH   = datetime(2024, 1, 1)
_LOG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "ATPAS-KeyGen"
_LOG_FILE = _LOG_DIR / "generated_keys.json"

# كلمة مرور المطوّر — غيّرها قبل التوزيع
_DEV_PASSWORD = "Rawaf@2026"

# ═══════════════════════════════════════════════════════════════════════════
# Core logic
# ═══════════════════════════════════════════════════════════════════════════

def generate_key(hardware_id: str, days_valid: int) -> str:
    hw_clean    = hardware_id.replace("-", "").upper()
    expiry_dt   = datetime.now() + timedelta(days=days_valid)
    expiry_days = (expiry_dt - _EPOCH).days
    expiry_hex  = f"{expiry_days:04X}"
    payload     = f"{hw_clean}:{expiry_hex}".encode("utf-8")
    sig = hmac.new(_HMAC_KEY, payload, hashlib.sha256).hexdigest()[:12].upper()
    return f"ATPAS-{expiry_hex}-{sig}"


def is_valid_hw_id(hw_id: str) -> bool:
    clean = hw_id.replace("-", "").strip()
    return len(clean) == 16 and all(c in "0123456789ABCDEF" for c in clean.upper())


# ═══════════════════════════════════════════════════════════════════════════
# Log helpers
# ═══════════════════════════════════════════════════════════════════════════

def _load_log() -> List[dict]:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not _LOG_FILE.exists():
        return []
    try:
        return json.loads(_LOG_FILE.read_text("utf-8"))
    except Exception:
        return []


def _save_log(entries: List[dict]) -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _LOG_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), "utf-8"
    )


def append_log(entry: dict) -> None:
    entries = _load_log()
    entries.insert(0, entry)
    _save_log(entries)


def export_log_csv(path: str) -> None:
    entries = _load_log()
    if not entries:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["date", "customer", "hw_id", "days", "expiry", "key"])
        w.writeheader()
        w.writerows(entries)


# ═══════════════════════════════════════════════════════════════════════════
# Font loader
# ═══════════════════════════════════════════════════════════════════════════

def _font_path(name: str) -> str:
    """Resolve font path — works both in dev and frozen EXE."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).parent.parent / "assets" / "fonts"
    return str(base / name)


def load_fonts() -> str:
    """Load Tajawal fonts and return the family name."""
    for fname in ("Tajawal-Regular.ttf", "Tajawal Bold.ttf"):
        path = _font_path(fname)
        if os.path.exists(path):
            QFontDatabase.addApplicationFont(path)
    return "Tajawal"


# ═══════════════════════════════════════════════════════════════════════════
# Password Gate Dialog
# ═══════════════════════════════════════════════════════════════════════════

class PasswordDialog(QDialog):
    def __init__(self, font_family: str) -> None:
        super().__init__()
        self.setWindowTitle("ATPAS — Key Generator")
        self.setFixedSize(440, 280)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)
        self._font = font_family
        self._ok   = False
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #1C3045, stop:1 #0D1C2B);
            border-bottom: 3px solid #C9921B;
        """)
        hl = QVBoxLayout(hdr)
        hl.setContentsMargins(24, 16, 24, 14)
        hl.setSpacing(4)

        t = QLabel("مولّد أكواد الترخيص")
        t.setStyleSheet(
            f"color:#FFF; font-size:17px; font-weight:800;"
            f"font-family:'{self._font}'; background:transparent;"
        )
        t.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        s = QLabel("ATPAS  —  Developer Tool  |  For Internal Use Only")
        s.setStyleSheet(
            f"color:#C9921B; font-size:10px; font-weight:500;"
            f"font-family:'{self._font}'; background:transparent;"
        )
        s.setLayoutDirection(Qt.LeftToRight)
        s.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        hl.addWidget(t)
        hl.addWidget(s)
        root.addWidget(hdr)

        # ── Body ─────────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background:#F5F0E8;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(30, 24, 30, 24)
        bl.setSpacing(10)

        lbl = QLabel("كلمة مرور المطوّر")
        lbl.setStyleSheet(
            f"font-family:'{self._font}'; font-size:13px;"
            f"font-weight:700; color:#152433;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bl.addWidget(lbl)

        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.Password)
        self._pw.setPlaceholderText("أدخل كلمة المرور...")
        self._pw.setAlignment(Qt.AlignRight)
        self._pw.setFixedHeight(42)
        self._pw.setStyleSheet(f"""
            QLineEdit {{
                font-family:'{self._font}'; font-size:13px;
                background:#FFF; border:1.5px solid #C3BBAA;
                border-radius:7px; padding:0px 12px; color:#121B28;
            }}
            QLineEdit:focus {{ border-color:#C9921B; border-width:2px; }}
        """)
        self._pw.returnPressed.connect(self._check)
        bl.addWidget(self._pw)

        self._err = QLabel("")
        self._err.setAlignment(Qt.AlignCenter)
        self._err.setFixedHeight(20)
        self._err.setStyleSheet(
            f"color:#B03030; font-family:'{self._font}'; font-size:12px;"
        )
        bl.addWidget(self._err)

        bl.addSpacing(4)

        btn = QPushButton("دخول")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(44)
        btn.setStyleSheet(f"""
            QPushButton {{
                font-family:'{self._font}'; font-size:14px; font-weight:800;
                background:#1C3045; color:#FFF; border:none;
                border-radius:8px; padding:0px;
                letter-spacing:1px;
            }}
            QPushButton:hover   {{ background:#2A4A63; }}
            QPushButton:pressed {{ background:#152433; }}
        """)
        btn.clicked.connect(self._check)
        bl.addWidget(btn)

        root.addWidget(body)

    def _check(self) -> None:
        if self._pw.text() == _DEV_PASSWORD:
            self._ok = True
            self.accept()
        else:
            self._err.setText("كلمة المرور غير صحيحة")
            self._pw.clear()
            self._pw.setFocus()

    def passed(self) -> bool:
        return self._ok


# ═══════════════════════════════════════════════════════════════════════════
# Duration options
# ═══════════════════════════════════════════════════════════════════════════

DURATIONS = [
    ("1 يوم   — تجريبي مجاني", 1),
    ("30 يوم  — شهر",          30),
    ("90 يوم  — 3 أشهر",       90),
    ("180 يوم — 6 أشهر",      180),
    ("365 يوم — سنة كاملة",    365),
    ("730 يوم — سنتان",        730),
    ("مدى الحياة (10 سنوات)",  3650),
]

# ═══════════════════════════════════════════════════════════════════════════
# Main Window
# ═══════════════════════════════════════════════════════════════════════════

class KeyGenWindow(QMainWindow):
    def __init__(self, font_family: str) -> None:
        super().__init__()
        self._font      = font_family
        self._last_key: str = ""
        self._log_cache: List[dict] = []   # in-memory cache, refreshed on generate
        self.setWindowTitle("ATPAS — مولّد أكواد الترخيص  |  Developer Tool")
        self.setMinimumSize(900, 680)
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_palette()
        self._build_ui()
        self._load_history()

    # ── Palette ────────────────────────────────────────────────────────────

    def _setup_palette(self) -> None:
        p = QPalette()
        p.setColor(QPalette.Window,          QColor("#F5F0E8"))
        p.setColor(QPalette.WindowText,      QColor("#121B28"))
        p.setColor(QPalette.Base,            QColor("#FFFFFF"))
        p.setColor(QPalette.AlternateBase,   QColor("#EDE8DD"))
        p.setColor(QPalette.Text,            QColor("#121B28"))
        p.setColor(QPalette.Button,          QColor("#1C3045"))
        p.setColor(QPalette.ButtonText,      QColor("#FFFFFF"))
        p.setColor(QPalette.Highlight,       QColor("#C9921B"))
        p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        self.setPalette(p)
        QApplication.instance().setPalette(p)

    # ── UI Build ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root_w = QWidget()
        self.setCentralWidget(root_w)
        root = QVBoxLayout(root_w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_body(), stretch=1)

    def _make_header(self) -> QWidget:
        hdr = QWidget()
        hdr.setFixedHeight(80)
        hdr.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #1C3045, stop:1 #0D1C2B);
            border-bottom: 3px solid #C9921B;
        """)
        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(24, 0, 24, 0)

        left = QVBoxLayout()
        left.setSpacing(3)
        t = QLabel("مولّد أكواد الترخيص — ATPAS")
        t.setStyleSheet(
            f"color:#FFF; font-size:18px; font-weight:800;"
            f"font-family:'{self._font}'; background:transparent;"
        )
        t.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        s = QLabel("Al-Rawaf Contracting  |  Developer Internal Tool  |  لا توزَّع هذه الأداة")
        s.setStyleSheet(
            f"color:#C9921B; font-size:10px; font-weight:500;"
            f"font-family:'{self._font}'; background:transparent;"
        )
        s.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        left.addWidget(t)
        left.addWidget(s)

        lay.addLayout(left)
        lay.addStretch()

        # Export CSV button
        exp_btn = self._make_btn("تصدير CSV", "#2B4A63", width=130)
        exp_btn.clicked.connect(self._export_csv)
        lay.addWidget(exp_btn)

        return hdr

    def _make_body(self) -> QWidget:
        body = QWidget()
        body.setStyleSheet("background:#F5F0E8;")
        main = QHBoxLayout(body)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(20)

        main.addWidget(self._make_left_panel(), stretch=0)
        main.addWidget(self._make_right_panel(), stretch=1)

        return body

    # ── Left panel: generation form ────────────────────────────────────────

    def _make_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setFixedWidth(380)
        panel.setStyleSheet("""
            QFrame {
                background:#FFFFFF;
                border-radius:12px;
                border:1px solid #D5CFBF;
            }
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(22, 22, 22, 22)
        lay.setSpacing(14)

        lay.addWidget(self._sec_label("① Hardware ID الخاص بالعميل"))

        self._hw_input = QLineEdit()
        self._hw_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._hw_input.setAlignment(Qt.AlignCenter)
        self._hw_input.setStyleSheet(self._field_style())
        self._hw_input.textChanged.connect(self._on_hw_changed)
        lay.addWidget(self._hw_input)

        self._hw_status = QLabel("")
        self._hw_status.setAlignment(Qt.AlignCenter)
        self._hw_status.setStyleSheet(f"font-family:'{self._font}'; font-size:11px; color:#5A6B7C;")
        lay.addWidget(self._hw_status)

        lay.addWidget(self._sep())
        lay.addWidget(self._sec_label("② اسم العميل / الجهة"))

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("مثال: م. محمد العتيبي — شركة البنية")
        self._name_input.setAlignment(Qt.AlignRight)
        self._name_input.setStyleSheet(self._field_style())
        lay.addWidget(self._name_input)

        lay.addWidget(self._sep())
        lay.addWidget(self._sec_label("③ مدة الترخيص"))

        self._dur_combo = QComboBox()
        for label, _ in DURATIONS:
            self._dur_combo.addItem(label)
        self._dur_combo.setCurrentIndex(3)   # default: سنة
        self._dur_combo.setStyleSheet(f"""
            QComboBox {{
                font-family:'{self._font}'; font-size:12px;
                background:#FFF; border:1.5px solid #C3BBAA;
                border-radius:6px; padding:8px 12px; color:#121B28;
                text-align: right;
            }}
            QComboBox:hover {{ border-color:#C9921B; }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox QAbstractItemView {{
                font-family:'{self._font}'; font-size:12px;
                background:#FFF; selection-background-color:#C9921B;
                selection-color:#FFF;
            }}
        """)
        lay.addWidget(self._dur_combo)

        lay.addWidget(self._sep())
        lay.addWidget(self._sec_label("④ تاريخ الانتهاء المتوقَّع"))

        self._expiry_label = QLabel("—")
        self._expiry_label.setAlignment(Qt.AlignCenter)
        self._expiry_label.setStyleSheet(f"""
            font-family:'{self._font}'; font-size:13px; font-weight:700;
            color:#152433; background:#EDE8DD;
            border-radius:6px; padding:8px;
        """)
        lay.addWidget(self._expiry_label)
        self._dur_combo.currentIndexChanged.connect(self._update_expiry)
        self._update_expiry()

        lay.addStretch()
        lay.addWidget(self._sep())

        gen_btn = self._make_btn("⚡  توليد كود الترخيص", "#2B7549", height=48, font_size=15)
        gen_btn.clicked.connect(self._generate)
        lay.addWidget(gen_btn)

        # Key output
        lay.addWidget(self._sec_label("الكود المُولَّد:"))

        self._key_display = QLineEdit()
        self._key_display.setReadOnly(True)
        self._key_display.setAlignment(Qt.AlignCenter)
        self._key_display.setPlaceholderText("يظهر هنا بعد الضغط على توليد...")
        self._key_display.setStyleSheet(f"""
            QLineEdit {{
                font-family:'Consolas','Courier New',monospace;
                font-size:14px; font-weight:700; letter-spacing:1px;
                background:#EEF8F2; border:2px solid #2B7549;
                border-radius:8px; padding:10px 12px; color:#152433;
            }}
        """)
        lay.addWidget(self._key_display)

        btn_row = QHBoxLayout()
        copy_btn = self._make_btn("نسخ الكود", "#C9921B", width=100, height=36, font_size=12)
        copy_btn.clicked.connect(self._copy_key)

        copy_msg_btn = self._make_btn("نسخ الرسالة", "#2B4A63", width=120, height=36, font_size=12)
        copy_msg_btn.clicked.connect(self._copy_whatsapp_msg)
        self._copy_msg_btn = copy_msg_btn

        wa_btn = self._make_btn("واتساب", "#25D366", width=100, height=36, font_size=12)
        wa_btn.clicked.connect(self._send_whatsapp)

        btn_row.addWidget(copy_btn)
        btn_row.addWidget(copy_msg_btn)
        btn_row.addWidget(wa_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        return panel

    # ── Right panel: history table ─────────────────────────────────────────

    def _make_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background:#FFFFFF;
                border-radius:12px;
                border:1px solid #D5CFBF;
            }
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        hdr_row = QHBoxLayout()
        title = QLabel("سجل الأكواد المُولَّدة")
        title.setStyleSheet(f"font-family:'{self._font}'; font-size:14px; font-weight:800; color:#152433;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        clear_btn = self._make_btn("مسح السجل", "#8A3030", height=30, font_size=11, width=110)
        clear_btn.clicked.connect(self._clear_log)
        hdr_row.addWidget(clear_btn)
        lay.addLayout(hdr_row)

        lay.addWidget(self._sep())

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["التاريخ", "العميل", "Hardware ID", "المدة", "الانتهاء", "كود الترخيص"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setLayoutDirection(Qt.RightToLeft)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                font-family:'{self._font}'; font-size:12px;
                background:#FFFFFF; alternate-background-color:#F7F3ED;
                gridline-color:#E5DFD3; border:none;
            }}
            QHeaderView::section {{
                font-family:'{self._font}'; font-size:12px; font-weight:700;
                background:#1C3045; color:#FFF;
                padding:8px 10px; border:none;
            }}
            QTableWidget::item {{ padding:6px 10px; }}
            QTableWidget::item:selected {{
                background:#C9921B; color:#FFF;
            }}
        """)
        lay.addWidget(self._table)

        # Stats row
        self._stats_label = QLabel("إجمالي الأكواد: 0")
        self._stats_label.setStyleSheet(f"font-family:'{self._font}'; font-size:11px; color:#5A6B7C;")
        self._stats_label.setAlignment(Qt.AlignLeft)
        lay.addWidget(self._stats_label)

        return panel

    # ── Helpers ────────────────────────────────────────────────────────────

    def _sec_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight)
        lbl.setStyleSheet(f"""
            font-family:'{self._font}'; font-size:12px; font-weight:700;
            color:#152433; padding-bottom:2px;
            border-bottom:1px solid #D5CFBF;
        """)
        return lbl

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#E5DFD3; max-height:1px;")
        return sep

    def _field_style(self) -> str:
        return f"""
            QLineEdit {{
                font-family:'{self._font}'; font-size:12px;
                background:#FFF; border:1.5px solid #C3BBAA;
                border-radius:6px; padding:9px 12px; color:#121B28;
            }}
            QLineEdit:focus {{ border-color:#C9921B; }}
        """

    def _make_btn(
        self, text: str, color: str, *,
        width: Optional[int] = None,
        height: int = 38,
        font_size: int = 13,
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        w_rule = f"min-width:{width}px; max-width:{width}px;" if width else ""
        btn.setStyleSheet(f"""
            QPushButton {{
                font-family:'{self._font}'; font-size:{font_size}px; font-weight:800;
                background:{color}; color:#FFF; border:none;
                border-radius:7px; padding:8px 14px;
                min-height:{height}px; {w_rule}
            }}
            QPushButton:hover   {{ background:{self._darker(color)}; }}
            QPushButton:pressed {{ background:{self._darker(color, 30)}; }}
        """)
        return btn

    @staticmethod
    def _darker(hex_color: str, amount: int = 15) -> str:
        c = QColor(hex_color)
        return c.darker(100 + amount).name()

    # ── Logic ──────────────────────────────────────────────────────────────

    # ── Renewal helper ─────────────────────────────────────────────────────────

    def _find_prev_license(self, hw_id: str) -> Optional[dict]:
        """Return the most recent log entry for this HW ID, or None."""
        clean = hw_id.replace("-", "").upper()
        for entry in self._log_cache:
            if entry.get("hw_id", "").replace("-", "").upper() == clean:
                return entry
        return None

    def _on_hw_changed(self, text: str) -> None:
        clean = text.strip().upper()
        if not clean:
            self._hw_status.setText("")
        elif is_valid_hw_id(clean):
            prev = self._find_prev_license(clean)
            if prev:
                customer = prev.get("customer", "—")
                expiry   = prev.get("expiry", "—")
                self._hw_status.setText(
                    f"جهاز مُسجَّل مسبقاً — العميل: {customer}  |  انتهاء سابق: {expiry}"
                )
                self._hw_status.setStyleSheet(
                    f"font-family:'{self._font}'; font-size:11px; color:#C9921B; font-weight:700;"
                )
            else:
                self._hw_status.setText("Hardware ID صحيح — جهاز جديد")
                self._hw_status.setStyleSheet(
                    f"font-family:'{self._font}'; font-size:11px; color:#2B7549; font-weight:700;"
                )
        else:
            self._hw_status.setText("يجب أن يكون 16 حرف hex (0-9 A-F) بصيغة XXXX-XXXX-XXXX-XXXX")
            self._hw_status.setStyleSheet(f"font-family:'{self._font}'; font-size:11px; color:#B03030;")

    def _update_expiry(self) -> None:
        _, days = DURATIONS[self._dur_combo.currentIndex()]
        expiry = datetime.now() + timedelta(days=days)
        self._expiry_label.setText(expiry.strftime("%Y-%m-%d"))

    def _generate(self) -> None:
        hw = self._hw_input.text().strip().upper()
        if not is_valid_hw_id(hw):
            QMessageBox.warning(
                self, "Hardware ID غير صحيح",
                "يرجى إدخال Hardware ID صحيح بصيغة:\nXXXX-XXXX-XXXX-XXXX\n(16 حرف هيكساديسيمال)"
            )
            return

        # ── فحص التجديد: هل هذا الجهاز لديه ترخيص سابق؟ ────────────────
        prev = self._find_prev_license(hw)
        if prev:
            prev_customer = prev.get("customer", "—")
            prev_expiry   = prev.get("expiry", "—")
            prev_days     = prev.get("days", "—")
            answer = QMessageBox.question(
                self,
                "تجديد ترخيص — جهاز مسجَّل مسبقاً",
                f"هذا الجهاز لديه ترخيص مُسجَّل في السجل:\n\n"
                f"  العميل السابق : {prev_customer}\n"
                f"  مدة الترخيص  : {prev_days} يوم\n"
                f"  تاريخ الانتهاء: {prev_expiry}\n\n"
                f"هل تريد توليد كود تجديد جديد لهذا الجهاز؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer != QMessageBox.Yes:
                return

        label, days = DURATIONS[self._dur_combo.currentIndex()]
        key        = generate_key(hw, days)
        expiry_dt  = datetime.now() + timedelta(days=days)
        customer   = self._name_input.text().strip() or "—"

        self._last_key = key
        self._key_display.setText(key)

        # Flash animation
        orig = self._key_display.styleSheet()
        self._key_display.setStyleSheet(orig.replace("#EEF8F2", "#D4F5E3"))
        QTimer.singleShot(400, lambda: self._key_display.setStyleSheet(orig))

        # Log + refresh cache
        entry = {
            "date":     datetime.now().strftime("%Y-%m-%d %H:%M"),
            "customer": customer,
            "hw_id":    hw,
            "days":     days,
            "expiry":   expiry_dt.strftime("%Y-%m-%d"),
            "key":      key,
        }
        append_log(entry)
        self._log_cache = _load_log()   # refresh so next HW check sees new entry
        self._insert_table_row(entry, prepend=True)
        self._update_stats()

    def _copy_key(self) -> None:
        if not self._last_key:
            return
        QApplication.clipboard().setText(self._last_key)
        btn = self.sender()
        if btn:
            orig = btn.text()
            btn.setText("تم النسخ")
            QTimer.singleShot(1500, lambda: btn.setText(orig))

    def _build_whatsapp_msg(self) -> str:
        """يبني نص الرسالة الجاهزة للإرسال عبر واتساب أو أي تطبيق."""
        customer = self._name_input.text().strip() or "عزيزي العميل"
        _, days  = DURATIONS[self._dur_combo.currentIndex()]
        expiry   = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        label    = DURATIONS[self._dur_combo.currentIndex()][0].strip()
        return (
            f"السلام عليكم {customer}،\n\n"
            f"شكراً لاشترائك نظام ATPAS.\n\n"
            f"كود الترخيص الخاص بجهازك:\n"
            f"{self._last_key}\n\n"
            f"نوع الترخيص: {label}\n"
            f"صالح حتى: {expiry}\n\n"
            f"خطوات التفعيل:\n"
            f"١. افتح البرنامج ATPAS.exe\n"
            f"٢. في نافذة التفعيل، الصق الكود أعلاه\n"
            f"٣. اضغط «تفعيل البرنامج»\n\n"
            f"ملاحظة: هذا الكود يعمل على جهازك الحالي فقط.\n"
            f"للدعم: jou1182@gmail.com\n\n"
            f"مع تحيات فريق الرواف 🏗"
        )

    def _copy_whatsapp_msg(self) -> None:
        """ينسخ رسالة واتساب الجاهزة إلى الحافظة بدون فتح المتصفح."""
        if not self._last_key:
            QMessageBox.information(self, "تنبيه", "ولّد الكود أولاً ثم اضغط نسخ الرسالة.")
            return
        msg = self._build_whatsapp_msg()
        QApplication.clipboard().setText(msg)
        btn = self._copy_msg_btn
        orig = btn.text()
        btn.setText("تم نسخ الرسالة")
        QTimer.singleShot(2000, lambda: btn.setText(orig))

    def _send_whatsapp(self) -> None:
        if not self._last_key:
            QMessageBox.information(self, "تنبيه", "ولّد الكود أولاً ثم اضغط واتساب.")
            return
        import urllib.parse
        msg = self._build_whatsapp_msg()
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(msg)}")

    # ── History table ──────────────────────────────────────────────────────

    def _load_history(self) -> None:
        self._log_cache = _load_log()
        for entry in self._log_cache:
            self._insert_table_row(entry)
        self._update_stats()

    def _insert_table_row(self, entry: dict, prepend: bool = False) -> None:
        row = 0 if prepend else self._table.rowCount()
        if prepend:
            self._table.insertRow(0)
        else:
            self._table.insertRow(row)

        cells = [
            entry.get("date", ""),
            entry.get("customer", ""),
            entry.get("hw_id", ""),
            f"{entry.get('days','')} يوم",
            entry.get("expiry", ""),
            entry.get("key", ""),
        ]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(str(text))
            item.setTextAlignment(Qt.AlignCenter)
            if col == 5:   # key column — monospace
                item.setFont(QFont("Consolas", 10))
                item.setForeground(QColor("#1C3045"))
            self._table.setItem(row, col, item)

    def _update_stats(self) -> None:
        count = self._table.rowCount()
        self._stats_label.setText(f"إجمالي الأكواد المُولَّدة: {count}")

    def _clear_log(self) -> None:
        r = QMessageBox.question(
            self, "تأكيد المسح",
            "هل تريد مسح سجل جميع الأكواد المُولَّدة؟\nلا يمكن التراجع عن هذا.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            _save_log([])
            self._log_cache = []
            self._table.setRowCount(0)
            self._update_stats()

    def _export_csv(self) -> None:
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير السجل", "atpas_keys_log.csv", "CSV Files (*.csv)"
        )
        if path:
            export_log_csv(path)
            QMessageBox.information(self, "تم", f"تم تصدير السجل إلى:\n{path}")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ATPAS-KeyGen")
    app.setOrganizationName("Al-Rawaf Contracting")

    font_family = load_fonts()
    base_font   = QFont(font_family, 11)
    app.setFont(base_font)

    # Password gate
    gate = PasswordDialog(font_family)
    if not gate.exec_() or not gate.passed():
        return 0

    window = KeyGenWindow(font_family)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
