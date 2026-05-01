#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Approval-state registry for source Word content files."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.json_manager import load_json, save_json
from utils.word_content_audit import WordContentAudit


_DEFAULT_APPROVAL_PATH = Path("templates/content_approval.json")

STATUS_NO_FILE = "no_file"
STATUS_PRESENT = "present"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_APPROVED = "approved"

STATUS_LABELS_AR = {
    STATUS_NO_FILE: "لا يوجد ملف",
    STATUS_PRESENT: "موجود غير معتمد",
    STATUS_NEEDS_REVIEW: "يحتاج مراجعة",
    STATUS_APPROVED: "معتمد",
}


@dataclass(frozen=True)
class ContentApprovalState:
    """Computed approval state for one code."""

    code_id: str
    status: str
    label_ar: str
    file_path: str = ""
    issue_count: int = 0
    approved_at: str = ""
    reviewer: str = ""
    notes: str = ""
    stale_approval: bool = False

    @property
    def approved(self) -> bool:
        return self.status == STATUS_APPROVED and not self.stale_approval


class ContentApprovalManager:
    """Read/write content approval metadata."""

    def __init__(self, path: str | Path = _DEFAULT_APPROVAL_PATH) -> None:
        self._path = Path(path)

    def load(self) -> dict[str, Any]:
        data = load_json(self._path, default={"approvals": {}})
        approvals = data.get("approvals", {})
        if not isinstance(approvals, dict):
            approvals = {}
        return {"approvals": approvals}

    def record_for(self, code_id: str) -> dict[str, Any]:
        return self.load().get("approvals", {}).get(code_id, {})

    def state_for(self, code_id: str, audit: WordContentAudit) -> ContentApprovalState:
        record = self.record_for(code_id)
        issue_count = len(audit.issues)

        if not audit.exists:
            return ContentApprovalState(
                code_id=code_id,
                status=STATUS_NO_FILE,
                label_ar=STATUS_LABELS_AR[STATUS_NO_FILE],
                file_path=audit.path,
                issue_count=issue_count,
                notes=str(record.get("notes", "")),
            )

        if issue_count:
            return ContentApprovalState(
                code_id=code_id,
                status=STATUS_NEEDS_REVIEW,
                label_ar=STATUS_LABELS_AR[STATUS_NEEDS_REVIEW],
                file_path=audit.path,
                issue_count=issue_count,
                approved_at=str(record.get("approved_at", "")),
                reviewer=str(record.get("reviewer", "")),
                notes=str(record.get("notes", "")),
            )

        current_hash = _sha256(Path(audit.path)) if audit.path else ""
        if record.get("status") == STATUS_APPROVED:
            stale = bool(record.get("file_sha256") and record.get("file_sha256") != current_hash)
            return ContentApprovalState(
                code_id=code_id,
                status=STATUS_NEEDS_REVIEW if stale else STATUS_APPROVED,
                label_ar="اعتماد قديم يحتاج مراجعة" if stale else STATUS_LABELS_AR[STATUS_APPROVED],
                file_path=audit.path,
                issue_count=issue_count,
                approved_at=str(record.get("approved_at", "")),
                reviewer=str(record.get("reviewer", "")),
                notes=str(record.get("notes", "")),
                stale_approval=stale,
            )

        return ContentApprovalState(
            code_id=code_id,
            status=STATUS_PRESENT,
            label_ar=STATUS_LABELS_AR[STATUS_PRESENT],
            file_path=audit.path,
            issue_count=issue_count,
            notes=str(record.get("notes", "")),
        )

    def approve(
        self,
        code_id: str,
        file_path: str | Path,
        *,
        reviewer: str = "",
        notes: str = "",
    ) -> None:
        data = self.load()
        approvals = data.setdefault("approvals", {})
        path = Path(file_path)
        now = datetime.now().isoformat(timespec="seconds")
        approvals[code_id] = {
            "status": STATUS_APPROVED,
            "approved_at": now,
            "updated_at": now,
            "reviewer": reviewer,
            "notes": notes,
            "file_path": str(path),
            "file_sha256": _sha256(path) if path.exists() else "",
        }
        save_json(data, self._path)

    def mark_needs_review(self, code_id: str, *, notes: str = "") -> None:
        data = self.load()
        approvals = data.setdefault("approvals", {})
        existing = approvals.get(code_id, {})
        existing.update({
            "status": STATUS_NEEDS_REVIEW,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "notes": notes or existing.get("notes", ""),
        })
        approvals[code_id] = existing
        save_json(data, self._path)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
