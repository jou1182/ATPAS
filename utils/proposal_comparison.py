#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Compare a draft proposal with the latest similar generated proposal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from utils.proposal_versions import ProposalVersionManager


@dataclass(frozen=True)
class ProposalComparison:
    """Diff between the current proposal and a previous similar one."""

    has_previous: bool
    previous_entry: dict[str, Any] = field(default_factory=dict)
    added_codes: list[str] = field(default_factory=list)
    removed_codes: list[str] = field(default_factory=list)
    shared_codes: list[str] = field(default_factory=list)
    previous_page_count: int = 0
    current_page_count: int = 0

    @property
    def page_delta(self) -> int:
        return self.current_page_count - self.previous_page_count

    @property
    def previous_label(self) -> str:
        return str(
            self.previous_entry.get("version_label")
            or self.previous_entry.get("proposal_id")
            or ""
        )

    @property
    def previous_timestamp(self) -> str:
        return str(
            self.previous_entry.get("timestamp_display")
            or self.previous_entry.get("timestamp")
            or ""
        )


def compare_with_latest_similar(
    *,
    manager: ProposalVersionManager,
    project_id: str,
    owner_id: str,
    current_codes: Iterable[str],
    current_page_count: int,
) -> ProposalComparison:
    """Find and compare against the newest saved proposal with same project/owner."""

    previous = find_latest_similar(manager, project_id=project_id, owner_id=owner_id)
    current = list(current_codes)
    if previous is None:
        return ProposalComparison(
            has_previous=False,
            current_page_count=int(current_page_count),
        )

    previous_codes = list(previous.get("codes", []))
    previous_set = set(previous_codes)
    current_set = set(current)

    return ProposalComparison(
        has_previous=True,
        previous_entry=previous,
        added_codes=[code for code in current if code not in previous_set],
        removed_codes=[code for code in previous_codes if code not in current_set],
        shared_codes=[code for code in current if code in previous_set],
        previous_page_count=_safe_int(previous.get("page_count"), 0),
        current_page_count=int(current_page_count),
    )


def find_latest_similar(
    manager: ProposalVersionManager,
    *,
    project_id: str,
    owner_id: str,
) -> dict[str, Any] | None:
    """Return newest proposal-version entry for the same project and owner."""

    for entry in reversed(manager.load()):
        if entry.get("project_id") == project_id and entry.get("owner_id") == owner_id:
            return entry
    return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
