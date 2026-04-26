#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ATPAS UI Theme — "المشغل المحترف"

Palette (v2 — Luxury Industrial):
  Bg (deep parchment)  #EDE7D9
  Surface (warm white) #FEFCF7
  Header (command navy)#152433
  Accent (rich gold)   #C9921B
  Text primary         #121B28
  Text secondary       #5A6B7C
  Border               #D5CFBF
  Error                #B03030
  Success              #2B7549
  Warning              #B56618
"""

import sys
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPalette, QFontDatabase


# ── Colour tokens — v2 Luxury Industrial ────────────────────────────
BG          = "#EDE7D9"      # deep warm parchment
SURFACE     = "#FEFCF7"      # warm white — clearly elevated above BG
HEADER      = "#152433"      # commanding deep navy
HEADER2     = "#0D1C2B"      # bottom of header gradient — richest depth
ACCENT      = "#C9921B"      # warmer, richer gold
ACCENT_DARK = "#A77218"      # pressed/deep gold
ACCENT_PALE = "#FAF0DC"      # gold tint for hover backgrounds
TEXT        = "#121B28"      # near-black text, maximum legibility
TEXT2       = "#5A6B7C"      # secondary — steel-blue grey
BORDER      = "#D5CFBF"      # stronger border
BORDER2     = "#C3BBAA"      # secondary border — more definition
ERROR       = "#B03030"
ERROR_PALE  = "#FEF0F0"
SUCCESS     = "#2B7549"      # richer engineering green
SUCCESS_PALE= "#EAF5EF"
WARNING     = "#B56618"
WARNING_PALE= "#FFF4E6"

# ── Metrics ────────────────────────────────────────────────────────
BASE_FONT_SIZE = 13
HEADER_FONT_SIZE = 15
TITLE_FONT_SIZE = 20
BADGE_FONT_SIZE = 11

# ── Fonts ──────────────────────────────────────────────────────────
MAIN_FONT = "'Tajawal', 'Segoe UI', 'Arial', 'Tahoma', sans-serif"
CODE_FONT = "'Consolas', 'Courier New', monospace"

def get_font(size: int = BASE_FONT_SIZE, weight: int = -1, italic: bool = False) -> QFont:
    """Helper to create a QFont instance with Tajawal as primary."""
    f = QFont("Tajawal")
    # Fallback list is handled by font-family in CSS, but for QFont we set main
    f.setPointSize(size)
    if weight != -1:
        f.setWeight(weight)
    f.setItalic(italic)
    return f


def load_fonts() -> None:
    """Load bundled fonts from assets/fonts/ to ensure portability."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(".")

    fonts_dir = base_path / "assets" / "fonts"
    if not fonts_dir.exists():
        return

    for font_file in fonts_dir.glob("*.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id == -1:
            print(f"Failed to load font: {font_file.name}")


def apply_palette(app) -> None:
    """Apply a QPalette so native widgets inherit the warm theme."""
    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(BG))
    pal.setColor(QPalette.WindowText,      QColor(TEXT))
    pal.setColor(QPalette.Base,            QColor(SURFACE))
    pal.setColor(QPalette.AlternateBase,   QColor(ACCENT_PALE))
    pal.setColor(QPalette.Text,            QColor(TEXT))
    pal.setColor(QPalette.BrightText,      QColor(SURFACE))
    pal.setColor(QPalette.Button,          QColor(SURFACE))
    pal.setColor(QPalette.ButtonText,      QColor(TEXT))
    pal.setColor(QPalette.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor(SURFACE))
    pal.setColor(QPalette.ToolTipBase,     QColor(HEADER))
    pal.setColor(QPalette.ToolTipText,     QColor(SURFACE))
    pal.setColor(QPalette.Midlight,        QColor(BORDER))
    pal.setColor(QPalette.Mid,             QColor(BORDER2))
    pal.setColor(QPalette.Dark,            QColor("#9A9590"))
    pal.setColor(QPalette.Shadow,          QColor("#00000022"))
    app.setPalette(pal)


def get_stylesheet() -> str:
    return f"""

/* ════════════════════════════════════════════
   BASE
   ════════════════════════════════════════════ */
QMainWindow, QDialog {{
    background: {BG};
    color: {TEXT};
}}

QWidget {{
    background: transparent;
    color: {TEXT};
    font-family: {MAIN_FONT};
    font-size: {BASE_FONT_SIZE}px;
}}

QWidget#mainCentral,
QWidget#mainContent {{
    background: {BG};
    color: {TEXT};
}}

/* Ensure dialogs are always readable even if parent areas are dark/transparent */
QDialog QWidget {{
    background: {SURFACE};
    color: {TEXT};
}}

QDialog QLabel {{
    color: {TEXT};
}}

QDialog QFrame {{
    color: {TEXT};
}}

QMessageBox {{
    background: {SURFACE};
}}

QMessageBox QLabel {{
    background: transparent;
    color: {TEXT};
    min-width: 320px;
    font-size: 13px;
    line-height: 1.45;
}}

QMessageBox QPushButton {{
    min-width: 92px;
    padding: 7px 18px;
}}

QTabWidget::pane {{
    background: {SURFACE};
    border: 1px solid {BORDER2};
    border-radius: 7px;
}}

QTabBar::tab {{
    background: #E9E3D6;
    color: {TEXT2};
    padding: 8px 16px;
    border: 1px solid {BORDER2};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    margin-left: 2px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: {SURFACE};
    color: {HEADER};
    border-top: 3px solid {ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background: {ACCENT_PALE};
    color: {ACCENT_DARK};
}}

/* ════════════════════════════════════════════
   GROUP BOXES — elevated card style
   ════════════════════════════════════════════ */
QGroupBox {{
    background: {SURFACE};
    border: 1px solid {BORDER2};
    border-radius: 10px;
    margin-top: 22px;
    padding: 14px 12px 12px 12px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    right: 14px;
    top: -10px;
    padding: 2px 12px 2px 12px;
    background: {ACCENT_PALE};
    color: {TEXT};
    font-weight: 700;
    font-size: 13px;
    border: 1px solid {BORDER2};
    border-radius: 5px;
    letter-spacing: 0.2px;
}}

/* ════════════════════════════════════════════
   CHECKBOXES
   ════════════════════════════════════════════ */
QCheckBox {{
    spacing: 8px;
    color: {TEXT};
    padding: 2px 0;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER2};
    background: {SURFACE};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    /* checkmark drawn via text trick — we paint it in code */
}}

QCheckBox::indicator:checked:disabled {{
    background: #9B7535;
    border-color: #9B7535;
}}

QCheckBox:disabled {{
    color: {TEXT2};
}}

/* ════════════════════════════════════════════
   BUTTONS — three tiers
   ════════════════════════════════════════════ */

/* Default */
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER2};
    border-radius: 7px;
    padding: 7px 22px;
    color: {TEXT};
    font-weight: 500;
    min-height: 30px;
}}

QPushButton:hover {{
    background: {ACCENT_PALE};
    border-color: {ACCENT};
    border-width: 1.5px;
    color: {ACCENT_DARK};
}}

QPushButton:focus {{
    border: 2px solid {ACCENT};
    color: {ACCENT_DARK};
}}

QPushButton:pressed {{
    background: #EDE4CC;
    border-color: {ACCENT_DARK};
    border-width: 2px;
}}

QPushButton:disabled {{
    background: #EDEAE4;
    color: #AAAAAA;
    border-color: #DDD8CE;
}}

/* Primary build button — the hero action */
QPushButton#buildBtn {{
    background: {SUCCESS};
    color: white;
    border: none;
    font-weight: 800;
    font-size: 15px;
    min-height: 44px;
    border-radius: 9px;
    letter-spacing: 0.4px;
    padding: 0 28px;
}}

QPushButton#buildBtn:hover {{
    background: #236040;
}}

QPushButton#buildBtn:focus {{
    border: 2px solid #E6D1A0;
    background: #236040;
}}

QPushButton#buildBtn:pressed {{
    background: #1B4E33;
}}

QPushButton#buildBtn:disabled {{
    background: #AFBFB8;
    color: #E2EDE9;
}}

/* Small category buttons (الكل / لا شيء) */
QPushButton[styleSheet*="font-size:10px"] {{
    min-height: 22px;
    padding: 2px 8px;
    font-size: 10px;
    border-radius: 5px;
}}

/* ════════════════════════════════════════════
   LINE EDIT / SEARCH
   ════════════════════════════════════════════ */
QLineEdit {{
    background: {SURFACE};
    border: 1.5px solid {BORDER2};
    border-radius: 7px;
    padding: 7px 14px;
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: white;
}}

QLineEdit:focus {{
    border: 2px solid {ACCENT};
    padding: 6px 13px;
}}

QLineEdit:hover {{
    border-color: {ACCENT};
}}

QLineEdit#codeSearchBox {{
    background: #FFF8EA;
}}

/* ════════════════════════════════════════════
   COMBO BOX
   ════════════════════════════════════════════ */
QComboBox {{
    background: {SURFACE};
    border: 1px solid {BORDER2};
    border-radius: 7px;
    padding: 5px 12px;
    color: {TEXT};
    min-height: 28px;
}}

QComboBox:hover {{
    border-color: {ACCENT};
}}

QComboBox:focus {{
    border: 2px solid {ACCENT};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
    subcontrol-origin: padding;
    subcontrol-position: left center;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 8px;
}}

QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    outline: none;
    selection-background-color: {ACCENT_PALE};
    selection-color: {TEXT};
    padding: 4px;
}}

/* ════════════════════════════════════════════
   LIST WIDGETS
   ════════════════════════════════════════════ */
QListWidget {{
    background: #FDFCF8;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QListWidget:focus {{
    border-color: {ACCENT};
}}

QListWidget::item {{
    padding: 7px 10px;
    border-radius: 5px;
    color: {TEXT};
    border: none;
}}

QListWidget::item:selected {{
    background: {ACCENT_PALE};
    color: {TEXT};
    border-left: 4px solid {ACCENT};
    font-weight: 500;
}}

QListWidget::item:hover:!selected {{
    background: #F5F0E8;
}}

/* ════════════════════════════════════════════
   SCROLL BARS — thin, refined
   ════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: transparent;
    width: 7px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER2};
    border-radius: 3px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 7px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER2};
    border-radius: 3px;
    min-width: 28px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ════════════════════════════════════════════
   SCROLL AREA
   ════════════════════════════════════════════ */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ════════════════════════════════════════════
   SPIN BOX
   ════════════════════════════════════════════ */
QSpinBox {{
    background: {SURFACE};
    border: 1px solid {BORDER2};
    border-radius: 7px;
    padding: 4px 10px;
    color: {TEXT};
    min-height: 26px;
}}

QSpinBox:focus {{
    border: 2px solid {ACCENT};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 20px;
    border: none;
    background: {ACCENT_PALE};
    border-radius: 3px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {ACCENT};
}}

/* ════════════════════════════════════════════
   STATUS BAR — dark console feel
   ════════════════════════════════════════════ */
QStatusBar {{
    background: {HEADER};
    color: {ACCENT};
    font-size: 12px;
    font-weight: 500;
    padding: 3px 14px;
    border-top: 1px solid {HEADER2};
}}

QStatusBar::item {{
    border: none;
}}

/* ════════════════════════════════════════════
   PROGRESS BAR
   ════════════════════════════════════════════ */
QProgressBar {{
    background: {BORDER2};
    border-radius: 9px;
    border: none;
    height: 18px;
    text-align: center;
    color: {TEXT};
    font-size: 11px;
    font-weight: 700;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DARK},
        stop:0.6 {ACCENT},
        stop:1.0 #E0AA38);
    border-radius: 9px;
}}

/* ════════════════════════════════════════════
   DIALOG BUTTON BOX
   ════════════════════════════════════════════ */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ════════════════════════════════════════════
   TOOL TIPS
   ════════════════════════════════════════════ */
QToolTip {{
    background: {HEADER};
    color: {SURFACE};
    border: 1px solid {ACCENT};
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ════════════════════════════════════════════
   LABEL — special classes
   ════════════════════════════════════════════ */
QLabel {{
    background: transparent;
}}

/* ════════════════════════════════════════════
   FORM LAYOUT labels
   ════════════════════════════════════════════ */
QFormLayout QLabel {{
    font-weight: 500;
    color: {TEXT2};
}}

/* ════════════════════════════════════════════
   HORIZONTAL / VERTICAL LINE
   ════════════════════════════════════════════ */
QFrame[frameShape="4"],  /* HLine */
QFrame[frameShape="5"]   /* VLine */
{{
    border: none;
    border-top: 1px solid {BORDER};
    background: transparent;
}}

"""
