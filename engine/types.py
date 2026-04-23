#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared type definitions for ATPAS engine.

Using TypedDict gives:
• IDE auto-complete for code dict fields across the entire codebase.
• Static type-checker (mypy / pyright) catches typos at analysis time.
• Living documentation — the shape of the data is explicit.

All fields are optional (total=False) because codes arriving from registry
JSON may have missing keys during early development or import.
"""

from __future__ import annotations

from typing import List
from typing import TypedDict


class CodeEntry(TypedDict, total=False):
    """One entry from ``codes_registry.json["codes"]``."""

    code_id:           str          # e.g. "003-PIP-SEW"
    activity_name_ar:  str          # Arabic activity name
    activity_name_en:  str          # English activity name
    category:          str          # "001" … "005"
    network:           str          # "S", "W", "A", "R", "C", "T"
    page_count:        int          # estimated pages in source docx
    image_count:       int          # estimated images in source docx
    sequence_order:    int          # display/sort order within proposal
    status:            str          # "active" | "inactive" | "deprecated"
    project_ids:       List[str]    # which projects this code belongs to
    applicable_owners: List[str]    # empty list = any owner allowed
    dependencies:      List[str]    # other code_ids that must be included
    excavation_type:   str          # mutually-exclusive group tag
    source_docx:       str          # filename in templates/source_documents/


class OwnerSpec(TypedDict, total=False):
    """One entry from ``metadata/owner_specifications/<id>.json``
    and ``master_config.json["owner_specifications"]``."""

    owner_id:          str
    owner_name_ar:     str          # Arabic display name (master_config key)
    owner_name_en:     str          # English display name (master_config key)
    name_ar:           str          # legacy alias kept for compatibility
    name_en:           str          # legacy alias kept for compatibility
    network:           str
    mandatory_codes:   List[str]
    forbidden_codes:   List[str]
    contact:           str


# Convenience alias used in function signatures throughout the engine
CodeRegistry = dict[str, CodeEntry]
