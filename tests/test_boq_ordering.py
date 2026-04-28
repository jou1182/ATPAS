# tests/test_boq_ordering.py
"""Tests for BOQ-order-preserving dependency resolution."""
import pytest
from engine.dependency_resolver import DependencyResolver


@pytest.fixture
def simple_codes():
    """5 codes, no dependencies."""
    return {
        "001-SUR-BASE": {"sequence_order": 1, "dependencies": []},
        "002-EXC-FINE": {"sequence_order": 2, "dependencies": []},
        "003-PIP-SEW":  {"sequence_order": 3, "dependencies": []},
        "004-TST-LEK":  {"sequence_order": 4, "dependencies": []},
        "005-BKF-SND":  {"sequence_order": 5, "dependencies": []},
    }


@pytest.fixture
def dep_codes():
    """003-PIP-SEW requires 001-SUR-BASE and 002-EXC-FINE."""
    return {
        "001-SUR-BASE": {"sequence_order": 1, "dependencies": []},
        "002-EXC-FINE": {"sequence_order": 2, "dependencies": []},
        "003-PIP-SEW":  {"sequence_order": 3, "dependencies": ["001-SUR-BASE", "002-EXC-FINE"]},
        "004-TST-LEK":  {"sequence_order": 4, "dependencies": []},
        "005-BKF-SND":  {"sequence_order": 5, "dependencies": []},
    }


def test_boq_order_no_deps_preserved(simple_codes):
    resolver = DependencyResolver(simple_codes)
    boq = ["003-PIP-SEW", "001-SUR-BASE", "005-BKF-SND"]
    result = resolver.resolve_with_order(boq, boq)
    assert result == ["003-PIP-SEW", "001-SUR-BASE", "005-BKF-SND"]


def test_missing_dep_injected_before_needing_code(dep_codes):
    resolver = DependencyResolver(dep_codes)
    boq = ["003-PIP-SEW", "004-TST-LEK"]
    result = resolver.resolve_with_order(boq, boq)
    assert result.index("001-SUR-BASE") < result.index("003-PIP-SEW")
    assert result.index("002-EXC-FINE") < result.index("003-PIP-SEW")
    assert result.index("003-PIP-SEW") < result.index("004-TST-LEK")


def test_boq_order_among_non_dep_codes_preserved(dep_codes):
    resolver = DependencyResolver(dep_codes)
    boq = ["004-TST-LEK", "001-SUR-BASE", "002-EXC-FINE", "003-PIP-SEW"]
    result = resolver.resolve_with_order(boq, boq)
    assert result[0] == "004-TST-LEK"
    assert result.index("001-SUR-BASE") < result.index("003-PIP-SEW")
    assert result.index("002-EXC-FINE") < result.index("003-PIP-SEW")


def test_dep_already_in_boq_not_duplicated(dep_codes):
    resolver = DependencyResolver(dep_codes)
    boq = ["001-SUR-BASE", "002-EXC-FINE", "003-PIP-SEW"]
    result = resolver.resolve_with_order(boq, boq)
    assert result.count("001-SUR-BASE") == 1
    assert result.count("002-EXC-FINE") == 1


def test_empty_boq_returns_empty(simple_codes):
    resolver = DependencyResolver(simple_codes)
    result = resolver.resolve_with_order([], [])
    assert result == []


def test_single_item_boq(simple_codes):
    resolver = DependencyResolver(simple_codes)
    result = resolver.resolve_with_order(["002-EXC-FINE"], ["002-EXC-FINE"])
    assert result == ["002-EXC-FINE"]


def test_unknown_code_in_boq_skipped(simple_codes):
    resolver = DependencyResolver(simple_codes)
    boq = ["001-SUR-BASE", "UNKNOWN-CODE", "003-PIP-SEW"]
    result = resolver.resolve_with_order(boq, boq)
    assert "UNKNOWN-CODE" not in result
    assert "001-SUR-BASE" in result
    assert "003-PIP-SEW" in result


def test_extra_selected_codes_appended_at_end(dep_codes):
    resolver = DependencyResolver(dep_codes)
    selected = ["001-SUR-BASE", "003-PIP-SEW", "005-BKF-SND"]
    boq      = ["003-PIP-SEW", "001-SUR-BASE"]
    result = resolver.resolve_with_order(selected, boq)
    assert "005-BKF-SND" in result
    boq_indices = [result.index(c) for c in ["003-PIP-SEW", "001-SUR-BASE"] if c in result]
    assert result.index("005-BKF-SND") > max(boq_indices)


def test_existing_resolve_unaffected(dep_codes):
    resolver = DependencyResolver(dep_codes)
    result = resolver.resolve(["003-PIP-SEW"])
    assert result == ["001-SUR-BASE", "002-EXC-FINE", "003-PIP-SEW"]
