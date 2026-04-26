#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the ATPAS system health report."""

from __future__ import annotations

from pathlib import Path

from utils.system_health import build_system_health_report


def _registry() -> dict:
    return {
        "metadata": {"version": "test"},
        "codes": {
            "001-SUR-BASE": {
                "code_id": "001-SUR-BASE",
                "activity_name_ar": "مسح عام",
                "activity_name_en": "General Survey",
                "project_ids": ["wastewater"],
                "applicable_owners": ["nwc"],
                "network_types": ["S"],
                "sequence_order": 1,
                "dependencies": [],
                "page_count": 2,
                "source_document": "001-SUR-BASE.docx",
                "status": "active",
            }
        },
    }


def _config() -> dict:
    return {
        "projects": {"wastewater": {"name_ar": "صرف صحي"}},
        "owner_specifications": {"nwc": {"owner_name_ar": "الشركة الوطنية للمياه"}},
    }


def test_health_report_counts_clean_data(tmp_path: Path) -> None:
    docs_dir = tmp_path / "source_documents"
    docs_dir.mkdir()
    (docs_dir / "001-SUR-BASE.docx").write_bytes(b"fake docx for health count")

    report = build_system_health_report(
        _registry(),
        _config(),
        {"presets": {"basic": {"codes": ["001-SUR-BASE"], "project_ids": ["wastewater"], "owner_id": "nwc"}}},
        docs_dir,
    )

    assert report.total_codes == 1
    assert report.active_codes == 1
    assert report.projects_count == 1
    assert report.owners_count == 1
    assert report.presets_count == 1
    assert report.linked_documents_count == 1
    assert report.missing_documents_count == 0
    assert report.errors == []


def test_health_report_flags_unknown_references(tmp_path: Path) -> None:
    registry = _registry()
    code = registry["codes"]["001-SUR-BASE"]
    code["project_ids"] = ["missing_project"]
    code["applicable_owners"] = ["missing_owner"]
    code["dependencies"] = ["999-BAD-REF"]

    report = build_system_health_report(registry, _config(), {"presets": {}}, tmp_path)

    messages = "\n".join(issue.message_ar for issue in report.errors)
    assert "مشاريع غير معرفة" in messages
    assert "جهات مالكة غير معرفة" in messages
    assert "أكواد غير موجودة" in messages


def test_health_report_accepts_inactive_status(tmp_path: Path) -> None:
    registry = _registry()
    registry["codes"]["001-SUR-BASE"]["status"] = "inactive"

    report = build_system_health_report(registry, _config(), {"presets": {}}, tmp_path)

    assert report.active_codes == 0
    assert report.inactive_codes == 1
    assert all("Unknown status" not in issue.message_ar for issue in report.errors)
