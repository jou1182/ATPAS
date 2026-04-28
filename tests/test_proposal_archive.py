#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for BuildHistoryManager.search() and extended save_entry() params.

Runs without PyQt5 — all PyQt5 imports are inside ui/ modules and are not
imported here.  Uses tmp_path so each test gets an isolated history file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ui.build_history import BuildHistoryManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mgr(tmp_path: Path) -> BuildHistoryManager:
    return BuildHistoryManager(history_path=tmp_path / "build_history.json")


def _populate(mgr: BuildHistoryManager) -> None:
    """Insert three distinct entries into the manager."""
    mgr.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE", "002-EXC-FINE"],
        output_file="/out/proposal_wastewater_nwc_001.docx",
        elapsed_seconds=3.2,
        page_count=10,
    )
    mgr.save_entry(
        project_id="water_supply",
        owner_id="moh",
        codes=["010-PIPE-STL"],
        output_file="/out/proposal_water_supply_moh_002.docx",
        elapsed_seconds=1.5,
        page_count=4,
    )
    mgr.save_entry(
        project_id="asphalt",
        owner_id="nwc",
        codes=["030-ASPH-BASE", "031-ASPH-WEAR"],
        output_file="/out/proposal_asphalt_nwc_003.docx",
        elapsed_seconds=2.0,
        page_count=6,
    )


# ---------------------------------------------------------------------------
# search() tests
# ---------------------------------------------------------------------------

def test_search_empty_query_returns_all(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results = mgr.search("")
    assert len(results) == 3


def test_search_query_matches_project_id(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results = mgr.search("nwc")
    # Both nwc entries match (owner_id contains "nwc")
    assert len(results) == 2
    for r in results:
        assert r["owner_id"] == "nwc"


def test_search_owner_id_filter(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results = mgr.search(owner_id="moh")
    assert len(results) == 1
    assert results[0]["owner_id"] == "moh"


def test_search_project_id_filter(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results = mgr.search(project_id="wastewater")
    assert len(results) == 1
    assert results[0]["project_id"] == "wastewater"


def test_search_nonexistent_returns_empty(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results = mgr.search("nonexistent_xyz_123")
    assert results == []


def test_search_on_empty_history_returns_empty(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    results = mgr.search()
    assert results == []


def test_search_matches_output_file_substring(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    # The output file for asphalt entry contains "asphalt"
    results = mgr.search("asphalt")
    assert len(results) >= 1
    assert any(r["project_id"] == "asphalt" for r in results)


def test_search_case_insensitive(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    results_lower = mgr.search("NWC")
    results_upper = mgr.search("nwc")
    assert len(results_lower) == len(results_upper)


def test_search_combined_query_and_owner_filter(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    # query matches "nwc" in owner_id, but also filter by owner_id="nwc"
    results = mgr.search("wastewater", owner_id="nwc")
    assert len(results) == 1
    assert results[0]["project_id"] == "wastewater"


# ---------------------------------------------------------------------------
# Extended save_entry() — template_vars and boq_item_count
# ---------------------------------------------------------------------------

def test_save_entry_stores_template_vars(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    tv = {"project_name": "مشروع الصرف", "tender_number": "T-2026-001"}
    mgr.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file="/out/p.docx",
        elapsed_seconds=1.0,
        page_count=2,
        template_vars=tv,
    )
    history = mgr.load()
    assert history[0]["template_vars"] == tv


def test_save_entry_stores_boq_item_count(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    mgr.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file="/out/p.docx",
        elapsed_seconds=1.0,
        page_count=2,
        boq_item_count=42,
    )
    history = mgr.load()
    assert history[0]["boq_item_count"] == 42


def test_save_entry_defaults_template_vars_to_none(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    mgr.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file="/out/p.docx",
        elapsed_seconds=1.0,
        page_count=2,
    )
    history = mgr.load()
    assert history[0].get("template_vars") is None


def test_save_entry_defaults_boq_item_count_to_zero(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    mgr.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file="/out/p.docx",
        elapsed_seconds=1.0,
        page_count=2,
    )
    history = mgr.load()
    assert history[0].get("boq_item_count", 0) == 0


# ---------------------------------------------------------------------------
# MAX_HISTORY cap
# ---------------------------------------------------------------------------

def test_history_capped_at_50(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    for i in range(55):
        mgr.save_entry(
            project_id="wastewater",
            owner_id="nwc",
            codes=[f"CODE-{i:03d}"],
            output_file=f"/out/p_{i}.docx",
            elapsed_seconds=0.1,
            page_count=1,
        )
    history = mgr.load()
    assert len(history) == 50


def test_newest_entry_first(tmp_path: Path) -> None:
    mgr = _mgr(tmp_path)
    _populate(mgr)
    history = mgr.load()
    # Last saved was "asphalt" — it should be first (newest first)
    assert history[0]["project_id"] == "asphalt"
