#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils.boq_coverage — compute_coverage() function."""

import pytest
from utils.boq_coverage import compute_coverage, CoverageResult


# ── Test 1: All BOQ items covered ─────────────────────────────────────────────

def test_all_covered():
    boq = ["001-SUR-BASE", "002-EXC-FINE", "003-PIPE-LAY"]
    selected = ["001-SUR-BASE", "002-EXC-FINE", "003-PIPE-LAY"]
    result = compute_coverage(boq, selected)
    assert result.total_boq == 3
    assert result.covered == ["001-SUR-BASE", "002-EXC-FINE", "003-PIPE-LAY"]
    assert result.uncovered == []
    assert result.extra == []
    assert result.coverage_pct == 100.0


# ── Test 2: None covered ──────────────────────────────────────────────────────

def test_none_covered():
    boq = ["001-SUR-BASE", "002-EXC-FINE"]
    selected = ["999-OTHER-A", "999-OTHER-B"]
    result = compute_coverage(boq, selected)
    assert result.total_boq == 2
    assert result.covered == []
    assert result.uncovered == ["001-SUR-BASE", "002-EXC-FINE"]
    assert set(result.extra) == {"999-OTHER-A", "999-OTHER-B"}
    assert result.coverage_pct == 0.0


# ── Test 3: Partial coverage ──────────────────────────────────────────────────

def test_partial_coverage():
    boq = ["001-SUR-BASE", "002-EXC-FINE", "003-PIPE-LAY", "004-MAN-HOLE"]
    selected = ["001-SUR-BASE", "003-PIPE-LAY", "999-EXTRA"]
    result = compute_coverage(boq, selected)
    assert result.total_boq == 4
    assert result.covered == ["001-SUR-BASE", "003-PIPE-LAY"]
    assert result.uncovered == ["002-EXC-FINE", "004-MAN-HOLE"]
    assert result.extra == ["999-EXTRA"]
    assert result.coverage_pct == 50.0


# ── Test 4: Empty BOQ order ────────────────────────────────────────────────────

def test_empty_boq_order():
    boq = []
    selected = ["001-SUR-BASE", "002-EXC-FINE"]
    result = compute_coverage(boq, selected)
    assert result.total_boq == 0
    assert result.covered == []
    assert result.uncovered == []
    # All selected codes are "extra" since BOQ is empty
    assert set(result.extra) == {"001-SUR-BASE", "002-EXC-FINE"}
    # Empty BOQ → 100% coverage (no items to miss)
    assert result.coverage_pct == 100.0


# ── Test 5: Extra codes (selected but not in BOQ) ─────────────────────────────

def test_extra_codes_only():
    boq = ["001-SUR-BASE"]
    selected = ["001-SUR-BASE", "EXTRA-001", "EXTRA-002", "EXTRA-003"]
    result = compute_coverage(boq, selected)
    assert result.covered == ["001-SUR-BASE"]
    assert result.uncovered == []
    assert set(result.extra) == {"EXTRA-001", "EXTRA-002", "EXTRA-003"}
    assert result.coverage_pct == 100.0


# ── Test 6: Coverage percentage calculation ────────────────────────────────────

def test_coverage_pct_calculation():
    # 3 out of 7 covered → 42.857...% → rounded to 42.9
    boq = [f"CODE-{i:03d}" for i in range(7)]
    selected = [f"CODE-{i:03d}" for i in range(3)]
    result = compute_coverage(boq, selected)
    assert result.total_boq == 7
    assert len(result.covered) == 3
    assert len(result.uncovered) == 4
    assert result.extra == []
    expected_pct = round(3 / 7 * 100, 1)
    assert result.coverage_pct == expected_pct


# ── Test 7: BOQ order is preserved in covered / uncovered ─────────────────────

def test_boq_order_preserved():
    boq = ["C", "A", "B"]
    selected = ["A", "C"]
    result = compute_coverage(boq, selected)
    # covered preserves BOQ order: C first, then A
    assert result.covered == ["C", "A"]
    assert result.uncovered == ["B"]


# ── Test 8: Duplicates in selected_codes do not inflate coverage ───────────────

def test_duplicates_in_selected_do_not_inflate():
    boq = ["001-SUR-BASE", "002-EXC-FINE"]
    selected = ["001-SUR-BASE", "001-SUR-BASE", "001-SUR-BASE"]
    result = compute_coverage(boq, selected)
    assert result.covered == ["001-SUR-BASE"]
    assert result.uncovered == ["002-EXC-FINE"]
    assert result.coverage_pct == 50.0
