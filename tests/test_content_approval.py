#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from utils.content_approval import (
    STATUS_APPROVED,
    STATUS_NEEDS_REVIEW,
    STATUS_NO_FILE,
    STATUS_PRESENT,
    ContentApprovalManager,
)
from utils.word_content_audit import WordContentAudit, WordContentIssue


def test_state_no_file(tmp_path: Path) -> None:
    manager = ContentApprovalManager(tmp_path / "approval.json")
    audit = WordContentAudit(code_id="001-SUR-BASE", path="", exists=False)

    state = manager.state_for("001-SUR-BASE", audit)

    assert state.status == STATUS_NO_FILE
    assert state.approved is False


def test_state_present_when_file_clean_but_not_approved(tmp_path: Path) -> None:
    file_path = tmp_path / "001-SUR-BASE.docx"
    file_path.write_bytes(b"doc")
    manager = ContentApprovalManager(tmp_path / "approval.json")
    audit = WordContentAudit(code_id="001-SUR-BASE", path=str(file_path), exists=True)

    state = manager.state_for("001-SUR-BASE", audit)

    assert state.status == STATUS_PRESENT


def test_approve_records_hash_and_state(tmp_path: Path) -> None:
    file_path = tmp_path / "001-SUR-BASE.docx"
    file_path.write_bytes(b"doc")
    manager = ContentApprovalManager(tmp_path / "approval.json")

    manager.approve("001-SUR-BASE", file_path, reviewer="QA", notes="ok")
    state = manager.state_for(
        "001-SUR-BASE",
        WordContentAudit(code_id="001-SUR-BASE", path=str(file_path), exists=True),
    )

    assert state.status == STATUS_APPROVED
    assert state.approved is True
    assert state.reviewer == "QA"
    assert state.notes == "ok"


def test_approved_file_change_requires_review(tmp_path: Path) -> None:
    file_path = tmp_path / "001-SUR-BASE.docx"
    file_path.write_bytes(b"doc")
    manager = ContentApprovalManager(tmp_path / "approval.json")
    manager.approve("001-SUR-BASE", file_path)

    file_path.write_bytes(b"changed")
    state = manager.state_for(
        "001-SUR-BASE",
        WordContentAudit(code_id="001-SUR-BASE", path=str(file_path), exists=True),
    )

    assert state.status == STATUS_NEEDS_REVIEW
    assert state.stale_approval is True


def test_audit_issue_forces_needs_review(tmp_path: Path) -> None:
    file_path = tmp_path / "001-SUR-BASE.docx"
    file_path.write_bytes(b"doc")
    manager = ContentApprovalManager(tmp_path / "approval.json")
    audit = WordContentAudit(
        code_id="001-SUR-BASE",
        path=str(file_path),
        exists=True,
        issues=[WordContentIssue("warning", "001-SUR-BASE", "عنوان مكرر")],
    )

    state = manager.state_for("001-SUR-BASE", audit)

    assert state.status == STATUS_NEEDS_REVIEW
