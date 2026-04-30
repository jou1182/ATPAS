#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for engine/logger.py."""

from __future__ import annotations

from engine.logger import generate_audit_trail, get_audit_history


def test_get_audit_history_reads_generated_records(tmp_path) -> None:
    audit_dir = tmp_path / "audit"
    generate_audit_trail(
        {
            "selected_codes": ["001-SUR-BASE"],
            "project_id": "wastewater",
            "owner_id": "nwc",
            "output_path": "proposal.docx",
            "status": "success",
            "processing_time_seconds": 1.25,
            "file_size_bytes": 1234,
            "error": None,
        },
        audit_dir=audit_dir,
    )

    history = get_audit_history(audit_dir)

    assert len(history) == 1
    assert history[0]["project_id"] == "wastewater"
    assert history[0]["selected_codes"] == ["001-SUR-BASE"]


def test_get_audit_history_skips_invalid_json(tmp_path) -> None:
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    (audit_dir / "audit_bad.json").write_text("{not json", encoding="utf-8")

    assert get_audit_history(audit_dir) == []
