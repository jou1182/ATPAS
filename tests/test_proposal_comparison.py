#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from utils.proposal_comparison import compare_with_latest_similar
from utils.proposal_versions import ProposalVersionManager


def _manager(tmp_path: Path) -> ProposalVersionManager:
    version_json = tmp_path / "version.json"
    version_json.write_text('{"version":"3.1","build_tag":"test"}', encoding="utf-8")
    return ProposalVersionManager(
        json_path=tmp_path / "versions.json",
        csv_path=tmp_path / "versions.csv",
        version_path=version_json,
    )


def _save(manager: ProposalVersionManager, tmp_path: Path, project: str, owner: str, codes: list[str], pages: int) -> None:
    output = tmp_path / f"{project}_{owner}_{len(codes)}.docx"
    output.write_bytes(b"x")
    manager.save_entry(
        project_id=project,
        owner_id=owner,
        codes=codes,
        output_file=output,
        elapsed_seconds=1,
        page_count=pages,
    )


def test_compare_returns_no_previous_when_history_empty(tmp_path: Path) -> None:
    comparison = compare_with_latest_similar(
        manager=_manager(tmp_path),
        project_id="wastewater",
        owner_id="nwc",
        current_codes=["A"],
        current_page_count=5,
    )

    assert comparison.has_previous is False
    assert comparison.current_page_count == 5


def test_compare_uses_latest_same_project_owner(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    _save(manager, tmp_path, "wastewater", "nwc", ["A", "B"], 10)
    _save(manager, tmp_path, "asphalt", "nwc", ["Z"], 3)
    _save(manager, tmp_path, "wastewater", "nwc", ["A", "C"], 12)

    comparison = compare_with_latest_similar(
        manager=manager,
        project_id="wastewater",
        owner_id="nwc",
        current_codes=["A", "B", "D"],
        current_page_count=15,
    )

    assert comparison.has_previous is True
    assert comparison.previous_page_count == 12
    assert comparison.page_delta == 3
    assert comparison.added_codes == ["B", "D"]
    assert comparison.removed_codes == ["C"]
    assert comparison.shared_codes == ["A"]
