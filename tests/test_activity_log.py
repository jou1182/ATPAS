#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the lightweight activity log."""

from __future__ import annotations

from pathlib import Path

from utils.activity_log import ActivityLog


def test_activity_log_appends_newest_first(tmp_path: Path) -> None:
    log = ActivityLog(tmp_path / "activity.json")

    log.append("الأول", {"a": 1})
    log.append("الثاني", {"b": 2})

    entries = log.latest()
    assert len(entries) == 2
    assert entries[0]["action_ar"] == "الثاني"
    assert entries[1]["details"] == {"a": 1}
