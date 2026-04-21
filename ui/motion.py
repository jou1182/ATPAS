#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared motion helpers with reduced-motion support.

ATPAS runs primarily on Windows desktops. We honor reduced-motion via:
1) Explicit app override env var: ATPAS_REDUCED_MOTION=1|0
2) Windows system setting: "Animate controls and elements inside windows"
"""

from __future__ import annotations

import ctypes
import os
from functools import lru_cache
from typing import Callable

from PyQt5.QtCore import QTimer

_TRUTHY = {"1", "true", "yes", "on"}
_FALSEY = {"0", "false", "no", "off"}
_SPI_GETCLIENTAREAANIMATION = 0x1042


@lru_cache(maxsize=1)
def prefers_reduced_motion() -> bool:
    """Return True when motion should be minimized for accessibility."""
    env = os.environ.get("ATPAS_REDUCED_MOTION", "").strip().lower()
    if env in _TRUTHY:
        return True
    if env in _FALSEY:
        return False

    if os.name == "nt":
        try:
            enabled = ctypes.c_int()
            ok = ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
                _SPI_GETCLIENTAREAANIMATION,
                0,
                ctypes.byref(enabled),
                0,
            )
            if ok:
                return enabled.value == 0
        except Exception:
            # If detection fails, keep animations on by default.
            return False

    return False


def motion_ms(normal_ms: int, reduced_ms: int = 1) -> int:
    """Return an accessibility-aware animation duration."""
    return max(1, reduced_ms if prefers_reduced_motion() else normal_ms)


def motion_single_shot(
    normal_ms: int,
    callback: Callable[[], None],
    reduced_ms: int = 0,
) -> None:
    """Schedule callback with motion-aware delay (or run now if reduced)."""
    if prefers_reduced_motion() and reduced_ms <= 0:
        callback()
        return
    QTimer.singleShot(motion_ms(normal_ms, reduced_ms=reduced_ms), callback)
