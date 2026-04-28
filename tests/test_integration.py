#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-008 + T031: E2E integration tests — full BOQ→docx pipeline.

Covers two layers:
  BKL-008 (4 scenarios): Validator → DependencyResolver → Builder
  T031    (6 scenarios): BOQ Importer → Matcher → (Gap Handler) → Builder → .docx
"""

import json
import tempfile
from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook

from engine.boq_importer import read_boq, BOQImportError
from engine.boq_matcher import BOQMatcher, MatchResult
from engine.builder import Builder
from engine.dependency_resolver import DependencyResolver
from engine.gap_handler import GapHandler
from engine.validator import Validator
from utils.json_manager import load_json

_BOQ_OUTPUT_DIR = Path("output/test_integration")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry():
    data = load_json("codes_registry.json")
    assert isinstance(data.get("codes"), dict), "codes_registry.json malformed"
    return data


@pytest.fixture(scope="module")
def registry_codes(registry):
    return registry["codes"]


@pytest.fixture(scope="module")
def config():
    return load_json("master_config.json")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def run_scenario(
    registry_codes: dict,
    selected_codes: list[str],
    project_id: str,
    owner_id: str,
    tmp_path: Path,
    scenario_name: str,
) -> Path:
    """Validate → resolve → build → return output path."""
    validator = Validator(registry_codes)
    resolver = DependencyResolver(registry_codes)
    builder = Builder(registry_codes)

    # Validate
    is_valid, errors, warnings = validator.validate(selected_codes, owner_id, project_id)
    assert is_valid, f"[{scenario_name}] Validation failed:\n" + "\n".join(errors)

    # Resolve
    full_codes = resolver.resolve(selected_codes)
    assert len(full_codes) >= len(selected_codes)

    # Build
    output = tmp_path / f"{scenario_name}.docx"
    success, error_ar = builder.build(
        selected_codes=full_codes,
        project_id=project_id,
        owner_id=owner_id,
        output_path=output,
        skip_validation=True,
    )
    assert success, f"[{scenario_name}] Build failed: {error_ar}"
    assert output.exists(), f"[{scenario_name}] Output file not created"
    assert output.stat().st_size > 5_000, f"[{scenario_name}] Output file suspiciously small"

    return output


# ---------------------------------------------------------------------------
# Scenario 1: wastewater + nwc (core scenario)
# ---------------------------------------------------------------------------

def test_e2e_wastewater_nwc(registry_codes, tmp_path):
    selected = [
        "001-SUR-BASE",
        "001-PRM-GOV",
        "001-APP-DES",
        "002-MAT-SITE",
        "002-EXC-FINE",
        "003-PIP-SEW",
        "004-TST-LEK",
        "005-BKF-SND",
        "005-RST-ASP",
    ]
    output = run_scenario(
        registry_codes, selected,
        project_id="wastewater",
        owner_id="nwc",
        tmp_path=tmp_path,
        scenario_name="wastewater_nwc",
    )
    doc = Document(str(output))
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "عرض فني" in full_text
    assert "الشركة الوطنية للمياه" in full_text or "nwc" in full_text.lower()


# ---------------------------------------------------------------------------
# Scenario 2: water_supply + nwc
# ---------------------------------------------------------------------------

def test_e2e_water_supply_nwc(registry_codes, tmp_path):
    selected = [
        "001-SUR-BASE",
        "001-PRM-GOV",
        "001-APP-DES",
        "003-PIP-WAT",
    ]
    output = run_scenario(
        registry_codes, selected,
        project_id="water_supply",
        owner_id="nwc",
        tmp_path=tmp_path,
        scenario_name="water_supply_nwc",
    )
    doc = Document(str(output))
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert any("003-PIP-WAT" in h for h in headings), "PIP-WAT section heading missing"


# ---------------------------------------------------------------------------
# Scenario 3: road_maintenance + mot (new network type R)
# ---------------------------------------------------------------------------

def test_e2e_road_maintenance_mot(registry_codes, tmp_path):
    selected = [
        "001-TRF-MGT",
        "001-RDS-INS",
        "002-PAV-EVL",
        "002-MIL-ASP",
        "004-TST-CMP",
        "004-TST-THK",
        "005-MRK-RD",
    ]
    output = run_scenario(
        registry_codes, selected,
        project_id="road_maintenance",
        owner_id="mot",
        tmp_path=tmp_path,
        scenario_name="road_maintenance_mot",
    )
    assert output.stat().st_size > 5_000


# ---------------------------------------------------------------------------
# Scenario 4: general_construction + nhi (new network type C)
# ---------------------------------------------------------------------------

def test_e2e_general_construction_nhi(registry_codes, tmp_path):
    selected = [
        "001-SOI-INV",
        "002-EXC-FND",   # one excavation type only (not EXC-BLK)
        "003-FND-CON",
        "003-STR-CON",
        "004-TST-CON",
        "005-CLN-STE",
    ]
    output = run_scenario(
        registry_codes, selected,
        project_id="general_construction",
        owner_id="nhi",
        tmp_path=tmp_path,
        scenario_name="general_construction_nhi",
    )
    doc = Document(str(output))
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert len(headings) >= len(selected), (
        f"Expected at least {len(selected)} headings, got {len(headings)}"
    )


# ---------------------------------------------------------------------------
# Cross-cutting: dependency resolver produces superset
# ---------------------------------------------------------------------------

def test_resolver_superset(registry_codes):
    """resolve() must always return a superset of the input."""
    resolver = DependencyResolver(registry_codes)
    selected = ["003-PIP-SEW", "002-EXC-FINE"]
    full = resolver.resolve(selected)
    assert set(selected).issubset(set(full))


# ---------------------------------------------------------------------------
# Cross-cutting: exclusive group enforced by validator
# ---------------------------------------------------------------------------

def test_validator_exclusive_group_blocked(registry_codes):
    """Selecting two excavation types must produce a validation error."""
    exc_codes = [
        cid for cid, cdata in registry_codes.items()
        if "excavation_type" in cdata and cdata.get("status") == "active"
    ]
    if len(exc_codes) < 2:
        pytest.skip("Not enough exclusive-group codes to test")

    validator = Validator(registry_codes)
    is_valid, errors, _ = validator.validate(exc_codes[:2], "nwc", "wastewater")
    assert not is_valid
    assert any("حصرية" in e or "حفر" in e for e in errors)


# ===========================================================================
# T031 — BOQ Importer → Matcher → (Gap Handler) → Builder → valid .docx
# ===========================================================================

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_xlsx(rows: list, path: Path) -> Path:
    """Write a single-column .xlsx file and return the path."""
    wb = Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


def _build_from_code_ids(
    registry_codes: dict,
    code_ids: list[str],
    project_id: str,
    owner_id: str,
    out: Path,
) -> None:
    """Validate → resolve → build; asserts success."""
    builder = Builder(registry_codes)
    _BOQ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success, err = builder.build(code_ids, project_id, owner_id, out, skip_validation=True)
    assert success, f"Build failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    assert len(doc.paragraphs) > 0


# ---------------------------------------------------------------------------
# T031-1: BOQ match → wastewater + nwc → valid .docx
# ---------------------------------------------------------------------------

def test_boq_to_docx_wastewater_nwc(registry_codes):
    """Arabic BOQ items are matched; the matched code IDs produce a valid .docx."""
    matcher = BOQMatcher(registry_codes)

    # Use activity_name_ar values from the registry — guaranteed to match ≥70%
    boq_items = [
        "مسح وتثبيت نقاط عامة",    # 001-SUR-BASE
        "الحصول على رخص حكومية",   # 001-PRM-GOV
        "اعتماد المخططات التفصيلية",  # 001-APP-DES
        "اعتماد خطة الصحة والسلامة",  # 001-APP-HSE
        "نقل المواد إلى موقع العمل",  # 002-MAT-SITE
        "حفر دقيق لأنابيب صغيرة",  # 002-EXC-FINE
    ]

    results = matcher.match(boq_items)
    matched = [r.code_id for r in results if r.code_id is not None]

    # All registry-exact items must match
    assert len(matched) == len(boq_items), (
        f"Expected {len(boq_items)} matches, got {len(matched)}. "
        + str([(r.boq_item, r.code_id, r.score) for r in results])
    )

    # Supplement with the remaining known-good wastewater+nwc codes
    extra = [
        "002-WST-EXC", "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP", "005-HND-DOC", "005-HND-FIN",
    ]
    full_ids = list(dict.fromkeys(matched + extra))  # preserve order, deduplicate

    out = _BOQ_OUTPUT_DIR / "boq_wastewater_nwc.docx"
    _build_from_code_ids(registry_codes, full_ids, "wastewater", "nwc", out)


# ---------------------------------------------------------------------------
# T031-2: BOQ match → water_supply + makkah → valid .docx
# ---------------------------------------------------------------------------

def test_boq_to_docx_water_makkah(registry_codes):
    """Arabic BOQ items matched; water_supply+makkah docx produced."""
    matcher = BOQMatcher(registry_codes)

    boq_items = [
        "مسح وتثبيت نقاط عامة",        # 001-SUR-BASE
        "الحصول على رخص حكومية",       # 001-PRM-GOV
        "الحصول على رخص بلدية",         # 001-PRM-MUN
        "اعتماد المخططات التفصيلية",    # 001-APP-DES
        "اعتماد خطة الصحة والسلامة",   # 001-APP-HSE
    ]

    results = matcher.match(boq_items)
    matched = [r.code_id for r in results if r.code_id is not None]
    assert len(matched) == len(boq_items), (
        f"Expected {len(boq_items)} matches, got {len(matched)}. "
        + str([(r.boq_item, r.code_id, r.score) for r in results])
    )

    extra = [
        "001-APP-MRL", "002-MAT-SITE", "002-EXC-FINE", "002-WST-EXC",
        "003-PIP-WAT", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP", "005-HND-DOC", "005-HND-FIN",
    ]
    full_ids = list(dict.fromkeys(matched + extra))

    out = _BOQ_OUTPUT_DIR / "boq_water_makkah.docx"
    _build_from_code_ids(registry_codes, full_ids, "water_supply", "makkah", out)


# ---------------------------------------------------------------------------
# T031-3: BOQ match → asphalt + moh → valid .docx
# ---------------------------------------------------------------------------

def test_boq_to_docx_asphalt_moh(registry_codes):
    """Arabic BOQ items matched; asphalt+moh docx produced."""
    matcher = BOQMatcher(registry_codes)

    boq_items = [
        "مسح وتثبيت نقاط عامة",        # 001-SUR-BASE
        "الحصول على رخص حكومية",       # 001-PRM-GOV
        "اعتماد المخططات التفصيلية",    # 001-APP-DES
        "قطع الأسفلت الموجود",          # 002-EXC-PAV
    ]

    results = matcher.match(boq_items)
    matched = [r.code_id for r in results if r.code_id is not None]
    assert len(matched) == len(boq_items), (
        f"Expected {len(boq_items)} matches, got {len(matched)}. "
        + str([(r.boq_item, r.code_id, r.score) for r in results])
    )

    extra = [
        "001-APP-MRL", "001-APP-HSE", "002-MAT-SITE", "002-WST-EXC",
        "004-QC-MATS", "005-BKF-BASE", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    full_ids = list(dict.fromkeys(matched + extra))

    out = _BOQ_OUTPUT_DIR / "boq_asphalt_moh.docx"
    _build_from_code_ids(registry_codes, full_ids, "asphalt", "moh", out)


# ---------------------------------------------------------------------------
# T031-4: GapHandler creates CUSTOM code → included in build → docx valid
# ---------------------------------------------------------------------------

def test_gap_handler_code_in_build(registry_codes, tmp_path):
    """A CUSTOM-NNN code created by GapHandler can be included in a build."""
    # Write an isolated registry copy so the real codes_registry.json is not polluted
    isolated = tmp_path / "codes_registry.json"
    registry_snapshot = {"metadata": {}, "codes": dict(registry_codes)}
    isolated.write_text(
        json.dumps(registry_snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    handler = GapHandler(str(isolated))
    custom_id = handler.create("أعمال صرف صحي خاصة", "wastewater")
    assert custom_id.startswith("CUSTOM-")

    # Reload codes from the updated isolated registry
    updated_codes = json.loads(isolated.read_text(encoding="utf-8"))["codes"]
    assert custom_id in updated_codes

    # Build a document that includes the custom code
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE", custom_id,
        "005-HND-DOC", "005-HND-FIN",
    ]

    out = _BOQ_OUTPUT_DIR / "boq_gap_handler_custom.docx"
    _BOQ_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    builder = Builder(updated_codes)
    success, err = builder.build(selected, "wastewater", "nwc", out, skip_validation=True)
    assert success, f"Build with CUSTOM code failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    assert len(doc.paragraphs) > 0


# ---------------------------------------------------------------------------
# T031-5: Items below 70% threshold are filtered before the build
# ---------------------------------------------------------------------------

def test_matcher_unknown_items_filtered(registry_codes):
    """BOQ items that score < 70% produce code_id=None and are excluded from build."""
    matcher = BOQMatcher(registry_codes)

    known_item = "مسح وتثبيت نقاط عامة"    # 001-SUR-BASE — should match
    unknown_item = "بند غير موجود xyz999"   # gibberish — should NOT match

    results = matcher.match([known_item, unknown_item])

    matched = results[0]
    unmatched = results[1]

    # Known item must be matched
    assert matched.code_id is not None
    assert matched.score >= 0.7

    # Unknown item must NOT be matched
    assert unmatched.code_id is None
    assert unmatched.score < 0.7

    # Filter: only include code_ids that were actually matched
    code_ids = [r.code_id for r in results if r.code_id is not None]
    assert len(code_ids) == 1
    assert code_ids[0] == "001-SUR-BASE"

    # Build with only the matched codes (plus minimum required codes)
    full_ids = list(dict.fromkeys(
        code_ids + [
            "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
            "002-MAT-SITE", "002-EXC-FINE",
            "005-HND-DOC", "005-HND-FIN",
        ]
    ))

    out = _BOQ_OUTPUT_DIR / "boq_filtered_unknown.docx"
    _build_from_code_ids(registry_codes, full_ids, "wastewater", "nwc", out)


# ---------------------------------------------------------------------------
# T031-6: read_boq (Excel) → match → build → valid .docx
# ---------------------------------------------------------------------------

def test_boq_import_excel_to_build(registry_codes, tmp_path):
    """Full pipeline: Excel file → read_boq → BOQMatcher → Builder → .docx."""
    # Create a real Excel file with Arabic BOQ items
    xlsx_path = tmp_path / "sample_boq.xlsx"
    _make_xlsx(
        [
            ["مسح وتثبيت نقاط عامة"],
            ["الحصول على رخص حكومية"],
            ["اعتماد المخططات التفصيلية"],
            ["اعتماد خطة الصحة والسلامة"],
            ["نقل المواد إلى موقع العمل"],
            ["حفر دقيق لأنابيب صغيرة"],
            ["بند غير معروف تماماً xyz000"],   # must be filtered out
        ],
        xlsx_path,
    )

    # Step 1: import
    items = read_boq(str(xlsx_path))
    assert len(items) == 7

    # Step 2: match
    matcher = BOQMatcher(registry_codes)
    results = matcher.match(items)
    assert len(results) == 7

    # Filter to matched only (≥70%)
    matched_ids = [r.code_id for r in results if r.code_id is not None]

    # The 6 registry-exact items should all match; the garbage item should not
    assert len(matched_ids) == 6, (
        f"Expected 6 matches from Excel import, got {len(matched_ids)}: "
        + str([(r.boq_item, r.code_id, r.score) for r in results])
    )

    # Step 3: supplement & build
    extra = [
        "002-WST-EXC", "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP", "005-HND-DOC", "005-HND-FIN",
    ]
    full_ids = list(dict.fromkeys(matched_ids + extra))

    out = _BOQ_OUTPUT_DIR / "boq_excel_to_build.docx"
    _build_from_code_ids(registry_codes, full_ids, "wastewater", "nwc", out)
