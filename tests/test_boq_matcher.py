#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import pytest
from engine.boq_matcher import BOQMatcher, MatchResult
from engine.gap_handler import GapHandler
from utils.json_manager import load_json


@pytest.fixture(scope="module")
def codes():
    return load_json("codes_registry.json")["codes"]


@pytest.fixture(scope="module")
def matcher(codes):
    return BOQMatcher(codes)


def test_exact_arabic_match(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].code_id == "001-SUR-BASE"
    assert results[0].score >= 0.9


def test_partial_match(matcher):
    results = matcher.match(["حفر"])
    assert results[0].code_id is not None
    assert results[0].score >= 0.0


def test_english_name_match(matcher):
    results = matcher.match(["General Surveying"])
    assert results[0].code_id == "001-SUR-BASE"
    assert results[0].score >= 0.7


def test_unknown_item_returns_none(matcher):
    results = matcher.match(["بند غير موجود أبداً xyz123"])
    assert results[0].code_id is None
    assert results[0].score < 0.7


def test_multiple_items(matcher):
    items = ["مسح وتثبيت نقاط عامة", "بند غير موجود xyz"]
    results = matcher.match(items)
    assert len(results) == 2
    assert results[0].code_id == "001-SUR-BASE"
    assert results[1].code_id is None


def test_result_has_boq_item(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].boq_item == "مسح وتثبيت نقاط عامة"


def test_empty_string_is_unknown(matcher):
    results = matcher.match(["   "])
    assert results[0].code_id is None


def test_score_between_0_and_1(matcher):
    results = matcher.match(["مسح"])
    assert 0.0 <= results[0].score <= 1.0


def test_known_item_is_not_new(matcher):
    results = matcher.match(["مسح وتثبيت نقاط عامة"])
    assert results[0].is_new is False


def test_unknown_item_is_not_new_by_default(matcher):
    results = matcher.match(["بند غير موجود xyz"])
    assert results[0].is_new is False


def test_score_never_exceeds_1(matcher):
    results = matcher.match(["حفر حفر حفر حفر حفر"])
    assert results[0].score <= 1.0


def test_creates_custom_code(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    handler = GapHandler(str(reg_path))
    code_id = handler.create("أعمال خاصة جداً", "wastewater")
    assert code_id.startswith("CUSTOM-")
    updated = json.loads(reg_path.read_text(encoding="utf-8"))
    assert code_id in updated["codes"]


def test_custom_ids_are_sequential(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    handler = GapHandler(str(reg_path))
    id1 = handler.create("بند أول", "wastewater")
    id2 = handler.create("بند ثاني", "wastewater")
    assert id1 == "CUSTOM-001"
    assert id2 == "CUSTOM-002"


def test_created_code_has_required_fields(tmp_path):
    registry = {"metadata": {}, "codes": {}}
    reg_path = tmp_path / "codes_registry.json"
    reg_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    handler = GapHandler(str(reg_path))
    code_id = handler.create("حفر خاص", "wastewater")
    updated = json.loads(reg_path.read_text(encoding="utf-8"))
    code = updated["codes"][code_id]
    assert code["activity_name_ar"] == "حفر خاص"
    assert code["status"] == "active"
    assert "wastewater" in code["project_ids"]
    assert code["is_custom"] is True
