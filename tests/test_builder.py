#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Builder integration tests + dependency-injection unit tests.

Run from the project root:
    python -m pytest tests/test_builder.py -v
"""

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from docx import Document

from engine.builder import Builder
from engine.dependency_resolver import DependencyResolver
from engine.validator import Validator
from utils.content_library import ContentLibrary
from utils.json_manager import load_json

_OUTPUT_DIR = Path("output/test_builds")


@pytest.fixture(scope="module")
def registry():
    return load_json("codes_registry.json")


@pytest.fixture(scope="module")
def codes(registry):
    return registry["codes"]


@pytest.fixture(scope="module")
def builder(codes):
    return Builder(codes)


# ---------------------------------------------------------------------------
# Scenario 1: wastewater + NWC + FINE excavation  →  valid .docx
# ---------------------------------------------------------------------------

def test_wastewater_nwc_fine(builder):
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE", "002-WST-EXC",
        "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "wastewater_nwc_fine.docx"
    success, err = builder.build(selected, "wastewater", "nwc", out)
    assert success, f"Build failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    assert len(doc.paragraphs) > 0


# ---------------------------------------------------------------------------
# Scenario 2: wastewater + NWC + OPEN excavation  →  valid .docx
# ---------------------------------------------------------------------------

def test_wastewater_nwc_open(builder):
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-OPEN", "002-WST-EXC",
        "003-PIP-SEW", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "wastewater_nwc_open.docx"
    success, err = builder.build(selected, "wastewater", "nwc", out)
    assert success, f"Build failed: {err}"
    assert out.exists()


# ---------------------------------------------------------------------------
# Scenario 3: water supply + Makkah + FINE excavation  →  valid .docx
# ---------------------------------------------------------------------------

def test_water_makkah_fine(builder):
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-PRM-MUN", "001-APP-DES",
        "001-APP-HSE", "001-APP-MRL",
        "002-MAT-SITE", "002-EXC-FINE", "002-WST-EXC",
        "003-PIP-WAT", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "water_makkah_fine.docx"
    success, err = builder.build(selected, "water_supply", "makkah", out)
    assert success, f"Build failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    # Heritage clause should have been added
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "التراث" in full_text or "تراث" in full_text


# ---------------------------------------------------------------------------
# Scenario 4: asphalt + MOH  →  valid .docx with compliance matrix
# ---------------------------------------------------------------------------

def test_asphalt_moh(builder):
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES",
        "001-APP-MRL", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-PAV", "002-WST-EXC",
        "004-QC-MATS",
        "005-BKF-BASE", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "asphalt_moh.docx"
    success, err = builder.build(selected, "asphalt", "moh", out)
    assert success, f"Build failed: {err}"
    assert out.exists()
    doc = Document(str(out))
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "الامتثال" in full_text


# ---------------------------------------------------------------------------
# Scenario 5: missing dependencies  →  build succeeds with warnings (not errors)
# ---------------------------------------------------------------------------

def test_missing_deps_build_with_warnings(builder):
    # 005-BKF-SND without its dependency 004-TST-LEK
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE", "002-EXC-FINE",
        "005-BKF-SND",   # missing: 003-PIP-SEW, 004-TST-LEK
        "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "missing_deps.docx"
    # Should build successfully (missing deps are warnings, not hard errors)
    success, err = builder.build(selected, "wastewater", "nwc", out)
    assert success, f"Expected build to succeed despite warnings, got: {err}"


# ---------------------------------------------------------------------------
# Scenario 6: conflicting excavation types  →  build rejected
# ---------------------------------------------------------------------------

def test_conflicting_excavation_rejected(builder):
    selected = [
        "001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE",
        "002-MAT-SITE",
        "002-EXC-FINE",   # conflict
        "002-EXC-OPEN",   # conflict
        "003-PIP-SEW",
    ]
    out = _OUTPUT_DIR / "conflict_exc.docx"
    success, err = builder.build(selected, "wastewater", "nwc", out)
    assert not success
    assert err is not None
    assert "حفر" in err


# ---------------------------------------------------------------------------
# Dependency injection — المحور 4
# ---------------------------------------------------------------------------

class TestBuilderDependencyInjection:
    """Verify Builder accepts pre-built collaborators instead of creating its own."""

    def test_default_creates_validator_and_resolver(self, codes) -> None:
        """Without injection, Builder instantiates its own collaborators."""
        b = Builder(codes)
        assert isinstance(b._validator, Validator)
        assert isinstance(b._resolver, DependencyResolver)

    def test_injected_validator_is_used(self, codes, tmp_path) -> None:
        """Injected Validator is called during build; internal one is NOT created."""
        mock_v = MagicMock(spec=Validator)
        mock_v.validate.return_value = (True, [], [])

        b = Builder(codes, validator=mock_v)
        assert b._validator is mock_v

        out = tmp_path / "di_validator.docx"
        b.build(["001-SUR-BASE"], "wastewater", "nwc", out)
        mock_v.validate.assert_called_once()

    def test_injected_resolver_is_used(self, codes, tmp_path) -> None:
        """Injected DependencyResolver is called during build."""
        mock_r = MagicMock(spec=DependencyResolver)
        mock_r.resolve.return_value = ["001-SUR-BASE"]

        b = Builder(codes, resolver=mock_r)
        assert b._resolver is mock_r

        out = tmp_path / "di_resolver.docx"
        b.build(["001-SUR-BASE"], "wastewater", "nwc", out, skip_validation=True)
        mock_r.resolve.assert_called_once_with(["001-SUR-BASE"])

    def test_injected_content_lib_is_used(self, codes, tmp_path) -> None:
        """Injected ContentLibrary controls whether real content is available."""
        mock_lib = MagicMock(spec=ContentLibrary)
        mock_lib.exists.return_value = False
        mock_lib.insert_into.return_value = False

        b = Builder(codes, content_lib=mock_lib)
        assert b._content_lib is mock_lib

        out = tmp_path / "di_content.docx"
        success, _ = b.build(["001-SUR-BASE"], "wastewater", "nwc", out,
                              skip_validation=True)
        assert success
        # insert_into should have been called for the single code
        mock_lib.insert_into.assert_called_once()

    def test_partial_injection_only_overrides_supplied(self, codes) -> None:
        """Only the supplied collaborator is overridden; others use defaults."""
        mock_v = MagicMock(spec=Validator)
        mock_v.validate.return_value = (True, [], [])

        b = Builder(codes, validator=mock_v)
        assert b._validator is mock_v
        assert isinstance(b._resolver, DependencyResolver)   # not mocked
        assert isinstance(b._content_lib, ContentLibrary)    # not mocked


# ---------------------------------------------------------------------------
# Performance: large document builds in < 5 seconds
# ---------------------------------------------------------------------------

def test_build_performance(builder):
    """60+ page document should build in under 5 seconds."""
    selected = [
        "001-SUR-BASE", "001-SUR-NET", "001-PRM-GOV", "001-PRM-ENV",
        "001-APP-DES", "001-APP-MRL", "001-APP-HSE",
        "002-MAT-SITE", "002-MAT-STORE", "002-EXC-OPEN", "002-WST-EXC", "002-WST-RECY",
        "003-PIP-WAT", "003-WLD-FLD",
        "004-TST-HYD", "004-TST-LEK", "004-QC-INSTALL",
        "005-BKF-SND", "005-BKF-SOL", "005-RST-ASP",
        "005-HND-DOC", "005-HND-TRN", "005-HND-FIN",
    ]
    out = _OUTPUT_DIR / "performance_test.docx"
    t0 = time.monotonic()
    success, err = builder.build(selected, "water_supply", "nwc", out)
    elapsed = time.monotonic() - t0
    assert success, f"Build failed: {err}"
    assert elapsed < 5.0, f"Build took {elapsed:.2f}s (limit 5s)"
    estimated_pages = builder.estimate_pages(selected)
    assert estimated_pages >= 60, f"Expected ≥60 pages, got {estimated_pages}"
