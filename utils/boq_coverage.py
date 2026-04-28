#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BOQ coverage analysis — computes which BOQ items are covered by the proposal."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CoverageResult:
    total_boq: int
    covered: list[str]          # code_ids in both boq_order and selected_codes
    uncovered: list[str]        # code_ids in boq_order but NOT in selected_codes
    extra: list[str]            # code_ids in selected_codes but NOT in boq_order
    coverage_pct: float         # covered / total_boq * 100


def compute_coverage(
    boq_order: list[str],
    selected_codes: list[str],
) -> CoverageResult:
    """Compute BOQ coverage stats.

    Args:
        boq_order: ordered list of code IDs from the imported Excel BOQ
        selected_codes: the codes the user selected in the UI

    Returns:
        CoverageResult with covered/uncovered/extra lists and percentage
    """
    boq_set = set(boq_order)
    selected_set = set(selected_codes)
    covered = [c for c in boq_order if c in selected_set]
    uncovered = [c for c in boq_order if c not in selected_set]
    extra = [c for c in selected_codes if c not in boq_set]
    pct = (len(covered) / len(boq_order) * 100) if boq_order else 100.0
    return CoverageResult(
        total_boq=len(boq_order),
        covered=covered,
        uncovered=uncovered,
        extra=extra,
        coverage_pct=round(pct, 1),
    )
