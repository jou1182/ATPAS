#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Regression tests for ui.motion helpers.

Locks the PyQt5-correct behavior of motion_single_shot(context=...) — the
Qt6-only static overload previously used here crashed the frozen app the
moment the first-run welcome dialog appeared (issue: "opens then closes").
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("ATPAS_REDUCED_MOTION", "0")   # force animations ON

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _qapp():
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv[:1])
    return app


def _wait(qapp, ms: int) -> None:
    """معالجة أحداث حقيقية لمدة ms — تسمح للمؤقتات بالنضج."""
    from PyQt5.QtTest import QTest
    QTest.qWait(ms)


def test_context_single_shot_fires_callback(qapp):
    from PyQt5.QtWidgets import QWidget

    from ui.motion import motion_single_shot

    host = QWidget()
    fired: list[int] = []
    motion_single_shot(5, lambda: fired.append(1), context=host)
    _wait(qapp, 300)
    assert fired == [1], "context-bound single shot must fire its callback"
    host.deleteLater()


def test_context_single_shot_survives_context_destruction(qapp):
    """Callback scheduled on a destroyed context must never run nor crash."""
    from PyQt5.QtWidgets import QWidget

    from ui.motion import motion_single_shot

    host = QWidget()
    fired: list[int] = []
    motion_single_shot(5000, lambda: fired.append(1), context=host)
    host.deleteLater()
    _wait(qapp, 60)
    assert fired == []


def test_reduced_motion_zero_reduced_runs_immediately(qapp, monkeypatch):
    from ui import motion

    monkeypatch.setattr(motion, "prefers_reduced_motion", lambda: True)
    fired: list[int] = []
    motion.motion_single_shot(1000, lambda: fired.append(1), reduced_ms=0)
    assert fired == [1], "reduced motion with no reduced_ms runs callback inline"
