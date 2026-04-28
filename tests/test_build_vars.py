#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for Feature 2: Dynamic Template Variables (الحقول الديناميكية).

Verifies that Builder.build() accepts template_vars and injects values
into the generated document cover page.

Run from the project root:
    python -m pytest tests/test_build_vars.py -v
"""

from pathlib import Path

import pytest
from docx import Document

from engine.builder import Builder
from utils.json_manager import load_json


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry():
    return load_json("codes_registry.json")


@pytest.fixture(scope="module")
def codes(registry):
    return registry["codes"]


@pytest.fixture(scope="module")
def builder(codes):
    return Builder(codes)


# A minimal selection that is valid for wastewater / nwc
_MINIMAL_CODES = [
    "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
    "002-MAT-SITE", "002-EXC-FINE", "002-WST-EXC",
    "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
    "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
    "005-HND-DOC", "005-HND-FIN",
]


def _full_text(doc: Document) -> str:
    """Return all paragraph text joined by spaces (cover page + sections)."""
    return " ".join(p.text for p in doc.paragraphs)


# ---------------------------------------------------------------------------
# Test 1: build succeeds when template_vars is provided
# ---------------------------------------------------------------------------

def test_build_succeeds_with_template_vars(builder, tmp_path):
    """Builder.build() must complete without error when template_vars is given."""
    out = tmp_path / "vars_basic.docx"
    vars_dict = {
        "project_name": "مشروع تجريبي",
        "tender_number": "MOH-2026-0041",
        "submission_date": "2026-05-01",
        "contract_value": "5,250,000 ريال",
        "engineer_name": "م. أحمد الغامدي",
    }
    success, err = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars=vars_dict,
    )
    assert success, f"Build failed unexpectedly: {err}"
    assert out.exists()


# ---------------------------------------------------------------------------
# Test 2: project_name from vars overrides metadata name on cover page
# ---------------------------------------------------------------------------

def test_cover_shows_project_name_from_vars(builder, tmp_path):
    """Cover page must contain the project_name value from template_vars."""
    out = tmp_path / "vars_project_name.docx"
    custom_name = "مشروع صرف صحي الرياض المرحلة الثالثة"
    success, _ = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={"project_name": custom_name},
    )
    assert success
    doc = Document(str(out))
    full = _full_text(doc)
    assert custom_name in full, (
        f"Expected project name '{custom_name}' in cover page, got:\n{full[:500]}"
    )


# ---------------------------------------------------------------------------
# Test 3: tender_number appears on the cover page when provided
# ---------------------------------------------------------------------------

def test_cover_shows_tender_number(builder, tmp_path):
    """Cover page must include the tender_number label when provided."""
    out = tmp_path / "vars_tender.docx"
    tender = "MOH-2026-0041"
    success, _ = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={"tender_number": tender},
    )
    assert success
    doc = Document(str(out))
    full = _full_text(doc)
    assert tender in full, (
        f"Expected tender number '{tender}' in cover page, got:\n{full[:500]}"
    )


# ---------------------------------------------------------------------------
# Test 4: contract_value appears on the cover page when provided
# ---------------------------------------------------------------------------

def test_cover_shows_contract_value(builder, tmp_path):
    """Cover page must include the contract_value when provided."""
    out = tmp_path / "vars_contract.docx"
    contract = "5,250,000 ريال"
    success, _ = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={"contract_value": contract},
    )
    assert success
    doc = Document(str(out))
    full = _full_text(doc)
    assert contract in full, (
        f"Expected contract value '{contract}' in cover page, got:\n{full[:500]}"
    )


# ---------------------------------------------------------------------------
# Test 5: template_vars=None still works (backward compatibility)
# ---------------------------------------------------------------------------

def test_build_backward_compat_no_vars(builder, tmp_path):
    """build() must work exactly as before when template_vars is not supplied."""
    out = tmp_path / "vars_none.docx"
    success, err = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
    )
    assert success, f"Backward-compat build failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    assert len(doc.paragraphs) > 0


# ---------------------------------------------------------------------------
# Test 6: engineer_name appears on cover page when provided
# ---------------------------------------------------------------------------

def test_cover_shows_engineer_name(builder, tmp_path):
    """Cover page must include the engineer_name prefixed with 'إعداد:'."""
    out = tmp_path / "vars_engineer.docx"
    engineer = "م. فيصل العتيبي"
    success, _ = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={"engineer_name": engineer},
    )
    assert success
    doc = Document(str(out))
    full = _full_text(doc)
    assert engineer in full, (
        f"Expected engineer name '{engineer}' in cover page, got:\n{full[:500]}"
    )


# ---------------------------------------------------------------------------
# Test 7: submission_date from vars overrides today's date on cover page
# ---------------------------------------------------------------------------

def test_cover_shows_custom_submission_date(builder, tmp_path):
    """Cover page must use submission_date from vars, not today's date."""
    out = tmp_path / "vars_date.docx"
    custom_date = "2027-12-31"
    success, _ = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={"submission_date": custom_date},
    )
    assert success
    doc = Document(str(out))
    full = _full_text(doc)
    assert custom_date in full, (
        f"Expected custom date '{custom_date}' in cover page, got:\n{full[:500]}"
    )


# ---------------------------------------------------------------------------
# Test 8: empty template_vars dict is handled gracefully (no crash, no change)
# ---------------------------------------------------------------------------

def test_build_with_empty_template_vars(builder, tmp_path):
    """Passing an empty dict for template_vars must not crash and must build ok."""
    out = tmp_path / "vars_empty.docx"
    success, err = builder.build(
        _MINIMAL_CODES, "wastewater", "nwc", out,
        skip_validation=True,
        template_vars={},
    )
    assert success, f"Build with empty template_vars failed: {err}"
    assert out.exists()
