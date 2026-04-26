#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for persistent proposal version registry."""

from __future__ import annotations

import hashlib
from pathlib import Path

from utils.proposal_versions import ProposalVersionManager


def test_save_entry_writes_json_and_csv(tmp_path: Path) -> None:
    output = tmp_path / "proposal.docx"
    output.write_bytes(b"proposal bytes")
    version_json = tmp_path / "version.json"
    version_json.write_text(
        '{"version":"3.1","build_tag":"3.1.20260426"}',
        encoding="utf-8",
    )
    manager = ProposalVersionManager(
        json_path=tmp_path / "proposal_versions.json",
        csv_path=tmp_path / "proposal_versions.csv",
        version_path=version_json,
    )

    entry = manager.save_entry(
        project_id="wastewater",
        owner_id="nwc",
        codes=["001-SUR-BASE", "002-EXC-FINE"],
        output_file=output,
        elapsed_seconds=2.345,
        page_count=8,
    )

    assert entry["version_label"] == "PV-000001"
    assert entry["code_count"] == 2
    assert entry["page_count"] == 8
    assert entry["app_version"] == "3.1"
    assert entry["app_build_tag"] == "3.1.20260426"
    assert entry["sha256"] == hashlib.sha256(b"proposal bytes").hexdigest()
    assert (tmp_path / "proposal_versions.json").exists()
    assert (tmp_path / "proposal_versions.csv").exists()


def test_save_entry_increments_version_number(tmp_path: Path) -> None:
    output = tmp_path / "proposal.docx"
    output.write_bytes(b"x")
    manager = ProposalVersionManager(
        json_path=tmp_path / "versions.json",
        csv_path=tmp_path / "versions.csv",
        version_path=tmp_path / "missing_version.json",
    )

    first = manager.save_entry(
        project_id="water_supply",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file=output,
        elapsed_seconds=1,
        page_count=3,
    )
    second = manager.save_entry(
        project_id="water_supply",
        owner_id="nwc",
        codes=["001-SUR-BASE"],
        output_file=output,
        elapsed_seconds=1,
        page_count=3,
    )

    assert first["version_number"] == 1
    assert second["version_number"] == 2
    assert [e["version_label"] for e in manager.load()] == ["PV-000001", "PV-000002"]
