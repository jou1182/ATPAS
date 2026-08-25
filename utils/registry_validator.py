#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Structural validation for codes_registry.json.

Provides:
    validate_registry(data)  — check schema without third-party dependencies.

The validator is intentionally *non-blocking*: it returns a list of issues
so the caller can decide whether to raise, log, or show a dialog.

Usage:
    from utils.registry_validator import validate_registry

    data = load_json("codes_registry.json")
    issues = validate_registry(data)
    for code_id, field, message in issues:
        logger.warning("Registry issue [%s].%s: %s", code_id, field, message)
"""

from __future__ import annotations

import logging
import re
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────────

_CODE_ID_RE = re.compile(r"^\d{3}-[A-Z]{2,8}-[A-Z]{2,8}$")

_REQUIRED_FIELDS: List[Tuple[str, type]] = [
    ("code_id",           str),
    ("activity_name_ar",  str),
    ("activity_name_en",  str),
    ("project_ids",       list),
    ("sequence_order",    int),
    ("status",            str),
]

_OPTIONAL_TYPED: List[Tuple[str, type]] = [
    ("dependencies",   list),
    ("has_images",     bool),
    ("image_count",    int),
    ("page_count",     int),
    ("applicable_owners", list),
    ("network_types",  list),
    ("tags",           list),
]

_ALLOWED_STATUSES = {"active", "inactive", "draft", "deprecated", "review", "archived"}

# Issue type alias: (code_id_or_"_registry", field, human-readable message)
Issue = Tuple[str, str, str]


# ── Public API ───────────────────────────────────────────────────────────────

def validate_registry(data: Any) -> List[Issue]:
    """Validate the full codes_registry.json dict.

    Args:
        data: Parsed JSON (from load_json).

    Returns:
        List of (scope, field, message) tuples — empty means no issues.
        *scope* is ``"_registry"`` for top-level issues, or the code_id.
    """
    issues: List[Issue] = []

    if not isinstance(data, dict):
        issues.append(("_registry", "_root", "Root must be a JSON object"))
        return issues

    # Top-level keys
    for key in ("metadata", "codes"):
        if key not in data:
            issues.append(("_registry", key, f"Missing required top-level key: '{key}'"))

    codes = data.get("codes")
    if not isinstance(codes, dict):
        if codes is not None:
            issues.append(("_registry", "codes", "'codes' must be a JSON object"))
        return issues

    for entry_key, entry in codes.items():
        issues.extend(_validate_entry(entry_key, entry))

    return issues


def validate_registry_strict(data: Any) -> None:
    """Like validate_registry but raises ValueError on the first issue found.

    Suitable for test assertions or startup checks where any schema error
    is considered fatal.
    """
    issues = validate_registry(data)
    if issues:
        scope, field, msg = issues[0]
        raise ValueError(f"Registry schema error [{scope}].{field}: {msg}")


# ── Internal helpers ─────────────────────────────────────────────────────────

def _validate_entry(key: str, entry: Any) -> List[Issue]:
    issues: List[Issue] = []

    if not isinstance(entry, dict):
        issues.append((key, "_entry", "Code entry must be a JSON object"))
        return issues

    # Required fields
    for field, expected_type in _REQUIRED_FIELDS:
        val = entry.get(field)
        if val is None:
            issues.append((key, field, f"Missing required field '{field}'"))
        elif not isinstance(val, expected_type):
            issues.append((
                key, field,
                f"'{field}' must be {expected_type.__name__}, got {type(val).__name__}"
            ))

    # code_id must match the canonical pattern.
    # Custom codes (is_custom: True, format 999-CUS-NNN) are exempt —
    # mirrors engine.validator._check_format so both validators agree.
    code_id = entry.get("code_id", "")
    if (
        isinstance(code_id, str) and code_id
        and not entry.get("is_custom")
        and not _CODE_ID_RE.match(code_id)
    ):
        issues.append((key, "code_id",
                        f"code_id '{code_id}' does not match NNN-AAA-BBB pattern"))

    # code_id in entry must equal the registry key
    if isinstance(code_id, str) and code_id and code_id != key:
        issues.append((key, "code_id",
                        f"code_id '{code_id}' does not match registry key '{key}'"))

    # status must be a known value
    status = entry.get("status")
    if isinstance(status, str) and status and status not in _ALLOWED_STATUSES:
        issues.append((key, "status",
                        f"Unknown status '{status}' — expected one of {sorted(_ALLOWED_STATUSES)}"))

    # Optional typed fields
    for field, expected_type in _OPTIONAL_TYPED:
        val = entry.get(field)
        if val is not None and not isinstance(val, expected_type):
            issues.append((
                key, field,
                f"'{field}' must be {expected_type.__name__} when present, got {type(val).__name__}"
            ))

    # Non-negative numeric fields
    for field in ("image_count", "page_count", "sequence_order"):
        val = entry.get(field)
        if isinstance(val, int) and val < 0:
            issues.append((key, field, f"'{field}' must be >= 0, got {val}"))

    # Non-empty string fields
    for field in ("activity_name_ar", "activity_name_en"):
        val = entry.get(field)
        if isinstance(val, str) and not val.strip():
            issues.append((key, field, f"'{field}' must not be blank"))

    return issues
