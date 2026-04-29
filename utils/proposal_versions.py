#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Persistent proposal version registry for ATPAS.

Unlike the quick UI build history, this registry is intended as a long-lived
institutional audit of every generated proposal.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.json_manager import load_json, save_json


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_JSON_PATH = _PROJECT_ROOT / "output" / "reports" / "proposal_versions.json"
_DEFAULT_CSV_PATH  = _PROJECT_ROOT / "output" / "reports" / "proposal_versions.csv"
_VERSION_PATH      = _PROJECT_ROOT / "version.json"


@dataclass(frozen=True)
class ProposalVersionEntry:
    """One generated proposal version."""

    proposal_id: str
    version_number: int
    version_label: str
    timestamp: str
    timestamp_display: str
    project_id: str
    owner_id: str
    codes: list[str]
    code_count: int
    page_count: int
    output_file: str
    output_name: str
    file_size_bytes: int
    sha256: str
    elapsed_seconds: float
    app_version: str
    app_build_tag: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "version_number": self.version_number,
            "version_label": self.version_label,
            "timestamp": self.timestamp,
            "timestamp_display": self.timestamp_display,
            "project_id": self.project_id,
            "owner_id": self.owner_id,
            "codes": self.codes,
            "code_count": self.code_count,
            "page_count": self.page_count,
            "output_file": self.output_file,
            "output_name": self.output_name,
            "file_size_bytes": self.file_size_bytes,
            "sha256": self.sha256,
            "elapsed_seconds": self.elapsed_seconds,
            "app_version": self.app_version,
            "app_build_tag": self.app_build_tag,
        }


class ProposalVersionManager:
    """Append-only registry for generated proposal versions."""

    def __init__(
        self,
        json_path: str | Path = _DEFAULT_JSON_PATH,
        csv_path: str | Path = _DEFAULT_CSV_PATH,
        version_path: str | Path = _VERSION_PATH,
    ) -> None:
        self._json_path = Path(json_path)
        self._csv_path = Path(csv_path)
        self._version_path = Path(version_path)

    def save_entry(
        self,
        *,
        project_id: str,
        owner_id: str,
        codes: list[str],
        output_file: str | Path,
        elapsed_seconds: float,
        page_count: int,
    ) -> dict[str, Any]:
        """Save one generated proposal version and return the stored entry."""

        history = self.load()
        # Monotonic max — survives JSON resets without duplicate IDs
        existing_max = max((e.get("version_number", 0) for e in history), default=0)
        version_number = existing_max + 1
        now = datetime.now()
        output_path = Path(output_file)
        output_abs = str(output_path.resolve())
        file_size = output_path.stat().st_size if output_path.exists() else 0
        digest = _sha256(output_path) if output_path.exists() else ""
        app_info = self._load_app_version()
        proposal_id = _proposal_id(
            version_number=version_number,
            project_id=project_id,
            owner_id=owner_id,
            timestamp=now,
        )

        entry = ProposalVersionEntry(
            proposal_id=proposal_id,
            version_number=version_number,
            version_label=f"PV-{version_number:06d}",
            timestamp=now.isoformat(timespec="seconds"),
            timestamp_display=now.strftime("%Y-%m-%d  %H:%M"),
            project_id=project_id,
            owner_id=owner_id,
            codes=list(codes),
            code_count=len(codes),
            page_count=int(page_count),
            output_file=output_abs,
            output_name=output_path.name,
            file_size_bytes=file_size,
            sha256=digest,
            elapsed_seconds=round(float(elapsed_seconds), 2),
            app_version=str(app_info.get("version", "")),
            app_build_tag=str(app_info.get("build_tag", "")),
        ).to_dict()

        history.append(entry)
        save_json({"proposal_versions": history}, self._json_path)
        self._write_csv(history)
        return entry

    def load(self) -> list[dict[str, Any]]:
        """Load all proposal versions, oldest first."""
        data = load_json(self._json_path, default={"proposal_versions": []})
        versions = data.get("proposal_versions", [])
        return versions if isinstance(versions, list) else []

    def latest(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return newest versions first."""
        return list(reversed(self.load()))[:limit]

    def _load_app_version(self) -> dict[str, Any]:
        return load_json(self._version_path, default={})

    def _write_csv(self, entries: list[dict[str, Any]]) -> None:
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        fields = [
            "version_label",
            "proposal_id",
            "timestamp_display",
            "project_id",
            "owner_id",
            "code_count",
            "page_count",
            "output_name",
            "output_file",
            "file_size_bytes",
            "elapsed_seconds",
            "app_version",
            "app_build_tag",
            "sha256",
            "codes",
        ]
        with open(self._csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for entry in entries:
                row = {field: entry.get(field, "") for field in fields}
                row["codes"] = " | ".join(entry.get("codes", []))
                writer.writerow(row)


def _proposal_id(version_number: int, project_id: str, owner_id: str, timestamp: datetime) -> str:
    date_part = timestamp.strftime("%Y%m%d")
    safe_project = _safe_token(project_id)
    safe_owner = _safe_token(owner_id)
    return f"ATPAS-{date_part}-{safe_project}-{safe_owner}-{version_number:06d}"


def _safe_token(value: str) -> str:
    cleaned = "".join(ch for ch in value.upper() if ch.isalnum())
    return cleaned[:14] or "NA"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
