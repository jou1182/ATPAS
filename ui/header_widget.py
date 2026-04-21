#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Branded application header for ATPAS.

Shows: logomark • Arabic product name • version • active codes counter.
Fixed height (~56 px). Dark navy background with gold accent.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget
from ui.motion import prefers_reduced_motion

# Pre-computed hex constants (sin/cos 30°, 60°) — avoids importing math
_S30 = 0.5       # sin(30°)
_C30 = 0.866     # cos(30°) = √3/2

_VERSION = "3.0"


class _AnimatedCounter(QLabel):
    """Counter label that smoothly interpolates to a new integer (exponential ease-out).

    When the code count jumps from, say, 4 → 12, the label visibly counts up
    rather than snapping instantly — a subtle but satisfying professional touch.
    """

    def __init__(self, parent=None) -> None:
        super().__init__("", parent)
        self._current: int = 0
        self._target:  int = 0
        self._timer = QTimer(self)
        self._timer.setInterval(16)   # ~60 fps
        self._timer.timeout.connect(self._step)

    def set_count(self, n: int) -> None:
        """Set target value; animation starts automatically."""
        if prefers_reduced_motion():
            self._target = n
            self._current = n
            self._timer.stop()
            self._refresh()
            return

        if n == self._target:
            return
        self._target = n
        if not self._timer.isActive():
            self._timer.start()

    def _step(self) -> None:
        diff = self._target - self._current
        if diff == 0:
            self._timer.stop()
            return
        # Move ~35% of remaining distance each frame → exponential ease-out
        delta = max(1, abs(diff) * 35 // 100)
        if diff > 0:
            self._current = min(self._current + delta, self._target)
        else:
            self._current = max(self._current - delta, self._target)
        self._refresh()

    def _refresh(self) -> None:
        n = self._current
        self.setText(f"◉  {n} كود نشط" if n else "")


def _make_hex_path(cx: float, cy: float, r: float) -> QPainterPath:
    """Flat-top regular hexagon centered at (cx, cy) with circumradius r.

    Vertex order (starting right, clockwise):
        0° right → 60° lower-right → 120° lower-left → 180° left →
        240° upper-left → 300° upper-right
    """
    path = QPainterPath()
    pts = [
        (cx + r,        cy),
        (cx + r * _S30, cy + r * _C30),
        (cx - r * _S30, cy + r * _C30),
        (cx - r,        cy),
        (cx - r * _S30, cy - r * _C30),
        (cx + r * _S30, cy - r * _C30),
    ]
    path.moveTo(*pts[0])
    for pt in pts[1:]:
        path.lineTo(*pt)
    path.closeSubpath()
    return path


class LogoMark(QWidget):
    """Engineering hexagonal seal — 50×50 px.

    Design language:
      • Flat-top hexagon (structural grid reference) filled deep navy
      • Bold gold ring border
      • Thin inner accent hexagon — engineering "cell" motif
      • Bold "A" letterform with apex accent dot
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(50, 50)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        gold   = QColor("#C9921B")
        gold2  = QColor("#E8C050")
        navy   = QColor("#152433")

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r_out  = min(w, h) / 2.0 - 2.0   # outer hex circumradius
        r_in   = r_out * 0.64             # inner accent ring

        # ── Outer hexagon fill (deep navy) ────────────────────────────
        p.setPen(Qt.NoPen)
        p.setBrush(navy)
        p.drawPath(_make_hex_path(cx, cy, r_out))

        # ── Gold border ring ──────────────────────────────────────────
        pen_ring = QPen(gold, 2.8)
        p.setPen(pen_ring)
        p.setBrush(Qt.NoBrush)
        p.drawPath(_make_hex_path(cx, cy, r_out - 0.5))

        # ── Thin inner accent hexagon ─────────────────────────────────
        pen_in = QPen(gold, 0.9)
        pen_in.setStyle(Qt.SolidLine)
        p.setPen(pen_in)
        p.drawPath(_make_hex_path(cx, cy, r_in))

        # ── Bold "A" letterform ───────────────────────────────────────
        r_a   = r_out * 0.52
        top_y = cy - r_a * 0.80
        bas_y = cy + r_a * 0.80
        bar_y = cy + r_a * 0.08
        hw    = r_a * 0.62    # half-width at base
        barhw = r_a * 0.40    # half-width of crossbar

        pen_a = QPen(gold2, 3.5)
        pen_a.setCapStyle(Qt.RoundCap)
        pen_a.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen_a)
        p.setBrush(Qt.NoBrush)

        # Left leg
        p.drawLine(int(cx), int(top_y), int(cx - hw), int(bas_y))
        # Right leg
        p.drawLine(int(cx), int(top_y), int(cx + hw), int(bas_y))
        # Crossbar
        p.drawLine(int(cx - barhw), int(bar_y), int(cx + barhw), int(bar_y))

        # Apex accent dot — surveying instrument reference
        p.setPen(Qt.NoPen)
        p.setBrush(gold2)
        apex_r = 2.2
        p.drawEllipse(
            int(cx - apex_r), int(top_y - apex_r),
            int(apex_r * 2),  int(apex_r * 2),
        )

        p.end()


class HeaderWidget(QWidget):
    """Dark branded header bar."""

    def __init__(self, active_codes: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(72)    # ↑ from 56 — more commanding presence
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup(active_codes)

    def _setup(self, active_codes: int) -> None:
        self.setStyleSheet("""
            HeaderWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1C3045,
                    stop:0.5 #152433,
                    stop:1   #0D1C2B);
                border-bottom: 4px solid #C9921B;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Engineering hexagonal logomark
        logo = LogoMark(self)

        # Product name — headline weight
        name_lbl = QLabel("نظام بناء العروض الفنية", self)
        name_lbl.setStyleSheet("""
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 800;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            background: transparent;
            letter-spacing: 0.3px;
        """)

        # Brand name — gold accent, clearly subordinate but distinct
        brand_lbl = QLabel("الرواف", self)
        brand_lbl.setStyleSheet("""
            color: #C9921B;
            font-size: 15px;
            font-weight: 700;
            background: transparent;
            padding-right: 6px;
            border-right: 2px solid #C9921B50;
        """)

        layout.addWidget(logo)
        layout.addWidget(name_lbl)
        layout.addWidget(brand_lbl)
        layout.addStretch()

        # Animated code counter — more visible, gold-tinted
        self._counter_lbl = _AnimatedCounter(self)
        self._set_counter(active_codes)
        self._counter_lbl.setStyleSheet("""
            color: #C8A860;
            font-size: 13px;
            font-weight: 600;
            background: transparent;
            letter-spacing: 0.4px;
        """)
        layout.addWidget(self._counter_lbl)

        # Version badge — more generous, clearly readable
        ver_lbl = QLabel(f"v{_VERSION}", self)
        ver_lbl.setStyleSheet("""
            color: #152433;
            background: #C9921B;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 12px;
            border-radius: 5px;
            letter-spacing: 0.5px;
        """)
        ver_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver_lbl)

    def _set_counter(self, n: int) -> None:
        self._counter_lbl.set_count(n)

    def update_counter(self, n: int) -> None:
        """Smoothly animate the counter to the new code count."""
        self._counter_lbl.set_count(n)
