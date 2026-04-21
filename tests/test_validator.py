#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
10 test scenarios for Validator + DependencyResolver (Phase 3 / US1).

Run from the project root:
    python -m pytest tests/test_validator.py -v
"""

import pytest

from engine.validator import Validator
from engine.dependency_resolver import DependencyResolver
from utils.json_manager import load_json


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def registry():
    return load_json("codes_registry.json")


@pytest.fixture(scope="module")
def codes(registry):
    return registry["codes"]


@pytest.fixture(scope="module")
def validator(codes):
    return Validator(codes)


@pytest.fixture(scope="module")
def resolver(codes):
    return DependencyResolver(codes)


# ---------------------------------------------------------------------------
# Scenario 1: Valid minimal wastewater set for NWC
# ---------------------------------------------------------------------------

def test_valid_wastewater_nwc(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE", "002-WST-EXC",
        "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    is_valid, errors, warnings = validator.validate(codes, "nwc", "wastewater")
    assert is_valid, f"Unexpected errors: {errors}"


# ---------------------------------------------------------------------------
# Scenario 2: Missing dependency — 005-BKF-SND requires 004-TST-LEK
# ---------------------------------------------------------------------------

def test_missing_dependency_warning(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE", "003-PIP-SEW",
        "005-BKF-SND",   # missing 004-TST-LEK
        "005-HND-FIN",
    ]
    is_valid, errors, warnings = validator.validate(codes, "nwc", "wastewater")
    # Missing deps are warnings, not hard errors
    dep_warning = any("004-TST-LEK" in w for w in warnings)
    assert dep_warning, f"Expected missing-dep warning for 004-TST-LEK, got: {warnings}"


# ---------------------------------------------------------------------------
# Scenario 3: Conflicting (mutually-exclusive) excavation types
# ---------------------------------------------------------------------------

def test_conflicting_excavation_types(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE",
        "002-EXC-FINE",    # conflict
        "002-EXC-OPEN",    # conflict
        "003-PIP-SEW",
    ]
    is_valid, errors, _ = validator.validate(codes, "nwc", "wastewater")
    assert not is_valid
    assert any("حفر" in e for e in errors)


# ---------------------------------------------------------------------------
# Scenario 4: Forbidden code for NWC (001-PRM-MUN is NWC-forbidden)
# ---------------------------------------------------------------------------

def test_forbidden_code_for_nwc(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-PRM-MUN",  # forbidden for NWC
        "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE", "003-PIP-SEW",
        "005-HND-FIN",
    ]
    is_valid, errors, _ = validator.validate(codes, "nwc", "wastewater")
    assert not is_valid
    assert any("001-PRM-MUN" in e for e in errors)


# ---------------------------------------------------------------------------
# Scenario 5: Non-existent code
# ---------------------------------------------------------------------------

def test_nonexistent_code(validator):
    codes = ["001-SUR-BASE", "999-XXX-ZZZ"]
    is_valid, errors, _ = validator.validate(codes, "nwc", "wastewater")
    assert not is_valid
    assert any("999-XXX-ZZZ" in e for e in errors)


# ---------------------------------------------------------------------------
# Scenario 6: Inactive code (injected into fixture copy)
# ---------------------------------------------------------------------------

def test_inactive_code(codes):
    patched = {**codes}
    patched["001-SUR-BASE"] = {**codes["001-SUR-BASE"], "status": "inactive"}
    v = Validator(patched)
    is_valid, errors, _ = v.validate(["001-SUR-BASE"], "nwc", "wastewater")
    assert not is_valid
    assert any("001-SUR-BASE" in e for e in errors)


# ---------------------------------------------------------------------------
# Scenario 7: Owner mismatch — 001-PRM-MUN is makkah-only, not nwc/moh
# ---------------------------------------------------------------------------

def test_owner_mismatch(validator):
    codes = ["001-SUR-BASE", "001-PRM-MUN"]  # 001-PRM-MUN only for makkah
    is_valid, errors, _ = validator.validate(codes, "nwc", "wastewater")
    assert not is_valid
    assert any("001-PRM-MUN" in e for e in errors)


# ---------------------------------------------------------------------------
# Scenario 8: Water supply project — valid set
# ---------------------------------------------------------------------------

def test_valid_water_supply_nwc(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES",
        "001-APP-HSE", "001-APP-MRL",
        "002-MAT-SITE", "002-EXC-OPEN", "002-WST-EXC",
        "003-PIP-WAT", "004-TST-HYD", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    is_valid, errors, warnings = validator.validate(codes, "nwc", "water_supply")
    assert is_valid, f"Unexpected errors: {errors}"


# ---------------------------------------------------------------------------
# Scenario 9: Asphalt project — valid set for MOH
# ---------------------------------------------------------------------------

def test_valid_asphalt_moh(validator):
    codes = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES",
        "001-APP-MRL", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-PAV", "002-WST-EXC",
        "004-QC-MATS",
        "005-BKF-BASE", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    is_valid, errors, warnings = validator.validate(codes, "moh", "asphalt")
    assert is_valid, f"Unexpected errors: {errors}"


# ---------------------------------------------------------------------------
# Scenario 10: DependencyResolver — resolve transitive closure
# ---------------------------------------------------------------------------

def test_dependency_resolver_transitive(resolver):
    # 003-PIP-SEW depends on an excavation type which depends on 002-MAT-SITE etc.
    full = resolver.resolve(["003-PIP-SEW"])
    assert "003-PIP-SEW" in full

    # suggest_missing: if we only have 003-PIP-SEW, what else is needed?
    missing = resolver.suggest_missing(["003-PIP-SEW"])
    assert "003-PIP-SEW" not in missing  # already selected
    # At minimum the dependencies chain should be non-empty
    assert len(missing) > 0


# ---------------------------------------------------------------------------
# Bonus: DependencyResolver does NOT infinite-loop on circular edge case
# ---------------------------------------------------------------------------

def test_resolver_no_infinite_loop(codes):
    # Inject a fake circular dependency to verify termination
    patched = {**codes}
    patched["TEST-A"] = {"dependencies": ["TEST-B"], "sequence_order": 99}
    patched["TEST-B"] = {"dependencies": ["TEST-A"], "sequence_order": 100}
    r = DependencyResolver(patched)
    result = r.resolve(["TEST-A"])
    assert "TEST-A" in result
    assert "TEST-B" in result  # both reachable without hanging
