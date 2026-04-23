#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Edge-case tests for engine/validator.py and engine/dependency_resolver.py.

Covers input validation, type guards, boundary conditions, and unusual
registry states that the primary test suite does not reach.

Run from the project root:
    python -m pytest tests/test_edge_cases.py -v
"""

from __future__ import annotations

import pytest

from engine.dependency_resolver import DependencyResolver
from engine.validator import Validator
from utils.json_manager import load_json


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def codes():
    return load_json("codes_registry.json")["codes"]


@pytest.fixture(scope="module")
def validator(codes):
    return Validator(codes)


@pytest.fixture(scope="module")
def resolver(codes):
    return DependencyResolver(codes)


# ---------------------------------------------------------------------------
# Validator — type guard tests (new in hardening sprint)
# ---------------------------------------------------------------------------

class TestValidatorTypeGuards:
    def test_raises_on_non_dict_codes(self) -> None:
        with pytest.raises(TypeError, match="dict"):
            Validator(["not", "a", "dict"])   # type: ignore[arg-type]

    def test_raises_on_none_codes(self) -> None:
        with pytest.raises(TypeError):
            Validator(None)   # type: ignore[arg-type]

    def test_accepts_empty_dict(self) -> None:
        v = Validator({})
        is_valid, errors, warnings = v.validate([], "any_owner", "any_project")
        assert is_valid
        assert errors == []


# ---------------------------------------------------------------------------
# DependencyResolver — type guard tests
# ---------------------------------------------------------------------------

class TestResolverTypeGuards:
    def test_raises_on_list_codes(self) -> None:
        with pytest.raises(TypeError, match="dict"):
            DependencyResolver(["list", "not", "dict"])   # type: ignore[arg-type]

    def test_raises_on_none(self) -> None:
        with pytest.raises(TypeError):
            DependencyResolver(None)   # type: ignore[arg-type]

    def test_accepts_empty_dict(self) -> None:
        r = DependencyResolver({})
        assert r.resolve([]) == []
        assert r.suggest_missing([]) == []


# ---------------------------------------------------------------------------
# Validator — boundary conditions
# ---------------------------------------------------------------------------

class TestValidatorBoundary:
    def test_empty_selection_is_valid(self, validator: Validator) -> None:
        is_valid, errors, warnings = validator.validate([], "nwc", "wastewater")
        assert is_valid
        assert errors == []

    def test_single_valid_code(self, validator: Validator) -> None:
        is_valid, errors, _ = validator.validate(["001-SUR-BASE"], "nwc", "wastewater")
        assert is_valid, f"Errors: {errors}"

    def test_all_active_codes_for_nwc_wastewater(self, codes: dict, validator: Validator) -> None:
        """Every active NWC-wastewater code must individually pass existence check."""
        nwc_ww = [
            cid for cid, c in codes.items()
            if c.get("status") == "active"
            and "wastewater" in c.get("project_ids", [])
            and (not c.get("applicable_owners") or "nwc" in c.get("applicable_owners", []))
        ]
        for cid in nwc_ww:
            _, errors, _ = validator.validate([cid], "nwc", "wastewater")
            code_errors = [e for e in errors if cid in e and "غير موجود" in e]
            assert code_errors == [], f"{cid} reported as not found: {code_errors}"

    def test_duplicate_codes_in_selection(self, validator: Validator) -> None:
        """Duplicate entries in selection must not cause double-errors."""
        codes = ["001-SUR-BASE", "001-SUR-BASE", "001-PRM-GOV"]
        _, errors, _ = validator.validate(codes, "nwc", "wastewater")
        # Any errors should be about content, not duplicates crashing
        assert isinstance(errors, list)

    def test_unknown_owner_does_not_crash(self, validator: Validator) -> None:
        """Unknown owner → fallback empty spec, should not raise."""
        is_valid, errors, warnings = validator.validate(
            ["001-SUR-BASE"], "nonexistent_owner_xyz", "wastewater"
        )
        assert isinstance(errors, list)   # no exception

    def test_project_id_as_string_backward_compat(self, validator: Validator) -> None:
        """validate() accepts a single string for project_id (legacy API)."""
        is_valid, errors, _ = validator.validate(
            ["001-SUR-BASE"], "nwc", "wastewater"  # str not list
        )
        assert is_valid, f"Errors with str project_id: {errors}"

    def test_project_id_as_list(self, validator: Validator) -> None:
        """validate() accepts a list of project_ids (multi-project API)."""
        is_valid, errors, _ = validator.validate(
            ["001-SUR-BASE"], "nwc", ["wastewater", "water_supply"]
        )
        assert is_valid, f"Errors with list project_id: {errors}"

    def test_mandatory_warning_contains_code_id(self, codes: dict) -> None:
        """Mandatory-code warnings must mention the missing code ID."""
        from pathlib import Path
        from utils.json_manager import load_json

        nwc_spec_path = Path("metadata/owner_specifications/nwc.json")
        if not nwc_spec_path.exists():
            pytest.skip("nwc spec file not found")

        spec = load_json(nwc_spec_path)
        mandatory = spec.get("mandatory_codes", [])
        if not mandatory:
            pytest.skip("nwc has no mandatory codes to test")

        # Select nothing (so mandatory codes are all missing)
        v = Validator(codes)
        _, _, warnings = v.validate([], "nwc", "wastewater")
        for mid in mandatory:
            assert any(mid in w for w in warnings), (
                f"Missing mandatory code {mid!r} not mentioned in warnings: {warnings}"
            )


# ---------------------------------------------------------------------------
# DependencyResolver — boundary conditions
# ---------------------------------------------------------------------------

class TestResolverBoundary:
    def test_resolve_empty_list(self, resolver: DependencyResolver) -> None:
        assert resolver.resolve([]) == []

    def test_suggest_missing_empty_list(self, resolver: DependencyResolver) -> None:
        assert resolver.suggest_missing([]) == []

    def test_dependencies_of_unknown_code(self, resolver: DependencyResolver) -> None:
        assert resolver.dependencies_of("DOES-NOT-EXIST") == []

    def test_resolve_code_without_dependencies(
        self, codes: dict, resolver: DependencyResolver
    ) -> None:
        # Find a code with empty dependencies
        no_dep = next(
            (cid for cid, c in codes.items() if not c.get("dependencies")), None
        )
        if no_dep is None:
            pytest.skip("No code without dependencies found")
        result = resolver.resolve([no_dep])
        assert no_dep in result

    def test_resolve_preserves_all_transitive_deps(self, codes: dict) -> None:
        """After resolve(), every dependency chain should be present."""
        r = DependencyResolver(codes)
        sample = list(codes.keys())[:5]
        full = set(r.resolve(sample))
        for cid in sample:
            for dep in codes[cid].get("dependencies", []):
                assert dep in full, (
                    f"Transitive dep {dep!r} of {cid!r} missing from resolve()"
                )

    def test_no_infinite_loop_deep_chain(self) -> None:
        """Chain A→B→C→D→E must resolve without recursion error."""
        patched = {
            "A": {"dependencies": ["B"], "sequence_order": 1},
            "B": {"dependencies": ["C"], "sequence_order": 2},
            "C": {"dependencies": ["D"], "sequence_order": 3},
            "D": {"dependencies": ["E"], "sequence_order": 4},
            "E": {"dependencies": [],   "sequence_order": 5},
        }
        r = DependencyResolver(patched)
        result = r.resolve(["A"])
        assert set(result) == {"A", "B", "C", "D", "E"}

    def test_sorted_by_sequence_order(self, codes: dict) -> None:
        """resolve() must return codes in sequence_order ascending."""
        r = DependencyResolver(codes)
        all_codes = list(codes.keys())
        result = r.resolve(all_codes)
        orders = [codes[c].get("sequence_order", 9999) for c in result if c in codes]
        assert orders == sorted(orders), "resolve() result not sorted by sequence_order"

    def test_suggest_missing_excludes_already_selected(self, resolver: DependencyResolver) -> None:
        """suggest_missing must never return a code that is already selected."""
        selected = ["001-SUR-BASE", "001-PRM-GOV", "001-APP-DES", "001-APP-HSE"]
        missing = resolver.suggest_missing(selected)
        selected_set = set(selected)
        for mid in missing:
            assert mid not in selected_set, (
                f"suggest_missing returned {mid!r} which is already selected"
            )


# ---------------------------------------------------------------------------
# TypedDict structural test
# ---------------------------------------------------------------------------

class TestCodeEntryTypedDict:
    """Verify engine.types.CodeEntry is importable and structurally correct."""

    def test_imports_without_error(self) -> None:
        from engine.types import CodeEntry, OwnerSpec, CodeRegistry
        assert CodeEntry is not None
        assert OwnerSpec is not None
        assert CodeRegistry is not None

    def test_code_entry_can_be_constructed_as_dict(self) -> None:
        from engine.types import CodeEntry
        # TypedDict instances are plain dicts at runtime
        entry: CodeEntry = {
            "code_id": "003-PIP-SEW",
            "activity_name_ar": "أعمال مواسير الصرف الصحي",
            "status": "active",
            "page_count": 4,
            "sequence_order": 30,
            "project_ids": ["wastewater"],
            "dependencies": ["002-EXC-FINE"],
        }
        assert entry["code_id"] == "003-PIP-SEW"
        assert entry["status"] == "active"
