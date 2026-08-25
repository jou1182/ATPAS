#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Theme contrast guard — locks WCAG AA for core token pairs.

Computes WCAG 2.x relative-luminance contrast ratios for the palette pairs
the UI actually renders, and fails if any drops below 4.5:1. This prevents
future token edits from silently regressing readability (audit P1-2).

Run:
    python -m pytest tests/test_theme_contrast.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _lin(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = sorted((_luminance(fg), _luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


# (fg token name, bg token name, minimum required ratio)
CORE_PAIRS = [
    ("TEXT", "BG", 7.0),          # primary reading surface — AAA
    ("TEXT", "SURFACE", 7.0),     # cards — AAA
    ("TEXT2", "SURFACE", 4.5),    # secondary text — AA
    ("TEXT2", "BG", 4.5),         # secondary on parchment — AA
    ("ACCENT_DARK", "SURFACE", 4.5),   # hover/pressed button text — AA
    ("WARNING", "WARNING_PALE", 4.5),  # warning banners — AA
    ("ERROR", "ERROR_PALE", 4.5),
    ("SUCCESS", "SUCCESS_PALE", 4.5),
    ("INFO", "INFO_PALE", 4.5),
    ("ACCENT", "HEADER", 4.5),    # gold on navy (header/tables)
    ("HEADER", "ACCENT", 4.5),    # navy on gold (version badge)
    ("NAVY_TEXT", "NAVY_DEEP", 4.5),   # preset buttons
    ("NAVY_MUTED", "NAVY_SOFT", 4.5),  # preset secondary text
]


@pytest.mark.parametrize("fg,bg,minimum", CORE_PAIRS, ids=[p[0] + "_on_" + p[1] for p in CORE_PAIRS])
def test_token_contrast_meets_minimum(fg: str, bg: str, minimum: float) -> None:
    from ui import theme

    ratio = contrast_ratio(getattr(theme, fg), getattr(theme, bg))
    assert ratio >= minimum, (
        f"theme.{fg} on theme.{bg} = {ratio:.2f}:1 — below {minimum}:1. "
        f"Darken {fg} or lighten {bg} (see docs/audit/ATPAS_UI_AUDIT_2026-08-25.md)."
    )


def test_no_white_on_gold() -> None:
    """White text on the gold accent was 2.76:1 — banned pair (audit P2-1)."""
    assert contrast_ratio("#FFFFFF", "#C9921B") < 4.5  # sanity: the pair IS bad
    from ui import theme

    assert contrast_ratio(theme.HEADER, theme.ACCENT) >= 4.5


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
