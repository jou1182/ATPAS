#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""BKL-008: E2E integration tests — 4 full build scenarios.

Each scenario:
  1. Loads registry + config
  2. Runs Validator
  3. Runs DependencyResolver
  4. Runs Builder.build() → produces a real .docx file
  5. Verifies file exists and is non-empty
"""

import tempfile
from pathlib import Path

import pytest
from docx import Document

from engine.builder import Builder
from engine.dependency_resolver import DependencyResolver
from engine.validator import Validator
from utils.json_manager import load_json

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
