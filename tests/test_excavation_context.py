#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spec 001 — Context-Aware Excavation Selection tests.

Verifies:
  - Excavation codes are classified by context (infrastructure/building/road)
  - Mixing conflicting excavation contexts blocks the build (error)
  - Project context mismatch produces a warning
  - Unclassified excavation codes produce a review warning
  - Building presets contain only building-compatible excavation

Run from the project root:
    python -m pytest tests/test_excavation_context.py -v
"""

import json
from pathlib import Path

import pytest

from engine.validator import Validator
from utils.json_manager import load_json

_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def registry():
    return load_json("codes_registry.json")


@pytest.fixture(scope="module")
def codes(registry):
    return registry["codes"]


@pytest.fixture(scope="module")
def validator(codes):
    return Validator(codes)


# ---------------------------------------------------------------------------
# التصنيف (FR-001)
# ---------------------------------------------------------------------------

def test_infrastructure_codes_classified(codes):
    """FINE/OPEN/TUNNEL هي حفر بنية تحتية."""
    assert codes["002-EXC-FINE"]["excavation_context"] == "infrastructure"
    assert codes["002-EXC-OPEN"]["excavation_context"] == "infrastructure"
    assert codes["002-EXC-TUNNEL"]["excavation_context"] == "infrastructure"


def test_building_codes_classified(codes):
    """FND/BLK + المساند الخمسة هي حفر مبانٍ."""
    assert codes["002-EXC-FND"]["excavation_context"] == "building"
    assert codes["002-EXC-BLK"]["excavation_context"] == "building"
    for cid in ("002-DEW-WTR", "002-SHR-SPT", "002-TRM-TRT",
                "002-SOL-RPL", "002-WPR-FND"):
        assert codes[cid]["excavation_context"] == "building", cid


def test_road_codes_classified(codes):
    """PAV/MIL حفر طرق."""
    assert codes["002-EXC-PAV"]["excavation_context"] == "road"
    assert codes["002-MIL-ASP"]["excavation_context"] == "road"


# ---------------------------------------------------------------------------
# منع الخلط (FR-005, FR-006, US3)
# ---------------------------------------------------------------------------

def test_mixing_infrastructure_and_building_blocks(validator, codes):
    """خلط حفر شبكات مع حفر مبانٍ = خطأ يمنع البناء."""
    selected = ["001-SUR-BASE", "002-EXC-FINE", "002-EXC-FND"]
    is_valid, errors, warnings = validator.validate(selected, "nwc", "wastewater")
    assert not is_valid, "خلط سياقين مختلفين يجب أن يمنع البناء"
    assert any("سياق الحفر" in e for e in errors), f"لم تظهر رسالة تعارض: {errors}"


def test_mixing_tunnel_and_building_blocks(validator):
    """خلط حفر نفقي مع حفر مبانٍ = خطأ (سيناريو US3: إنشاءات + نفقي)."""
    selected = ["002-EXC-TUNNEL", "002-EXC-FND"]
    is_valid, errors, warnings = validator.validate(selected, "nhi", "general_construction")
    assert not is_valid
    assert any("سياق الحفر" in e for e in errors)


def test_single_context_allowed(validator):
    """سياق واحد فقط = مسموح (حتى لو لم يطابق المشروع يبقى تحذيراً لا خطأ)."""
    selected = ["002-EXC-FND", "002-DEW-WTR", "002-SHR-SPT"]
    is_valid, errors, warnings = validator.validate(selected, "nhi", "general_construction")
    assert is_valid, f"حزمة مبانٍ كاملة يجب أن تكون صالحة: {errors}"


# ---------------------------------------------------------------------------
# مطابقة سياق المشروع (FR-002, FR-006)
# ---------------------------------------------------------------------------

def test_building_excavation_in_water_project_warns(validator):
    """حفر مبانٍ في مشروع مياه = تحذير سياق (وليس خطأ).

    نستدعي فحص السياق مباشرة لأن validate() يمنع الكود أولاً
    (غير مخصص لمشروع wastewater) — فحص السياق مستقل عنه.
    """
    errors: list[str] = []
    warnings: list[str] = []
    validator._check_excavation_context(["002-EXC-FND"], ["wastewater"], errors, warnings)
    assert not errors, f"تحذير سياق لا يمنع البناء: {errors}"
    assert any("لا يطابق سياق المشروع" in w for w in warnings), f"لا تحذير: {warnings}"


def test_infrastructure_excavation_in_building_project_warns(validator):
    """حفر بنية تحتية في مشروع إنشاءات = تحذير سياق."""
    errors: list[str] = []
    warnings: list[str] = []
    validator._check_excavation_context(
        ["002-EXC-FINE"], ["general_construction"], errors, warnings
    )
    assert not errors, f"تحذير سياق لا يمنع البناء: {errors}"
    assert any("لا يطابق سياق المشروع" in w for w in warnings), f"لا تحذير: {warnings}"


# ---------------------------------------------------------------------------
# أكواد غير مصنفة (FR-017)
# ---------------------------------------------------------------------------

def test_unclassified_excavation_code_warns(validator, codes):
    """كود حفر بلا سياق = تحذير مراجعة (لا يختار صامتاً)."""
    # 002-WST-EXC في فئة 002 لكن بلا excavation_context
    assert "excavation_context" not in codes["002-WST-EXC"]
    selected = ["002-WST-EXC"]
    is_valid, errors, warnings = validator.validate(selected, "nwc", "wastewater")
    assert is_valid
    assert any("بلا تصنيف سياق" in w for w in warnings), f"لا تحذير مراجعة: {warnings}"


# ---------------------------------------------------------------------------
# الأنماط الجاهزة (FR-008, SC-001/002/006)
# ---------------------------------------------------------------------------

def test_building_presets_contain_only_building_excavation(codes):
    """أنماط الإنشاءات تحتوي حفر مبانٍ فقط — لا حفر شبكات."""
    presets = load_json(_ROOT / "presets.json")["presets"]
    for name in ("gc_nhi_building", "gc_nhi_steel"):
        preset = presets[name]
        assert preset["project_ids"] == ["general_construction"]
        for cid in preset["codes"]:
            ctx = codes.get(cid, {}).get("excavation_context", "")
            if ctx:
                assert ctx == "building", (
                    f"{name}: {cid} بسياق {ctx} — يجب أن يكون building"
                )


def test_nwc_presets_contain_no_building_excavation(codes):
    """أنماط NWC لا تحتوي أي حفر مبانٍ."""
    presets = load_json(_ROOT / "presets.json")["presets"]
    for name, preset in presets.items():
        if preset.get("owner_id") != "nwc":
            continue
        for cid in preset["codes"]:
            ctx = codes.get(cid, {}).get("excavation_context", "")
            assert ctx != "building", f"{name}: {cid} حفر مبانٍ داخل نمط NWC"


def test_building_presets_build_without_errors(validator):
    """أنماط الإنشاءات تبني بدون أخطاء تحقق (SC-006)."""
    presets = load_json(_ROOT / "presets.json")["presets"]
    for name in ("gc_nhi_building", "gc_nhi_steel"):
        preset = presets[name]
        is_valid, errors, warnings = validator.validate(
            preset["codes"],
            preset["owner_id"],
            preset["project_ids"],
        )
        assert is_valid, f"{name} فشل: {errors}"


# ---------------------------------------------------------------------------
# اكتمال حزمة الحفر (FR-007, US4)
# ---------------------------------------------------------------------------

def test_new_building_codes_registered_in_registry(registry):
    """الأكواد الخمسة الجديدة موجودة في السجل ونشطة."""
    for cid in ("002-DEW-WTR", "002-SHR-SPT", "002-TRM-TRT",
                "002-SOL-RPL", "002-WPR-FND"):
        assert cid in registry["codes"], f"{cid} غير موجود"
        assert registry["codes"][cid]["status"] == "active"
        assert registry["codes"][cid]["excavation_context"] == "building"
