#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فهرس أرشفة سريع لسجل العروض — طبقة أداء وبحث فوق proposal_versions.json.

العقد المعماري (specs/004):
  * JSON يبقى **مصدر التبادل والتصدير** — لا يُستبدل.
  * هذا الفهرس المحلي يمنح بحثاً فورياً في آلاف العروض ورؤى تجميعية.
  * كل كتابة تمر مزدوجة: JSON + الفهرس (انظر ProposalVersionManager.save_entry).
  * الوصول المتزامن آمن: WAL + busy_timeout.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_JSON_PATH = _PROJECT_ROOT / "output" / "reports" / "proposal_versions.json"
_DEFAULT_DB_PATH = _PROJECT_ROOT / "output" / "reports" / "archive_index.db"

_SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS proposals (
    proposal_id      TEXT PRIMARY KEY,
    version_number   INTEGER,
    version_label    TEXT,
    timestamp        TEXT,
    timestamp_display TEXT,
    project_id       TEXT,
    owner_id         TEXT,
    codes_json       TEXT,
    code_count       INTEGER,
    page_count       INTEGER,
    output_file      TEXT,
    output_name      TEXT,
    file_size_bytes  INTEGER,
    sha256           TEXT,
    elapsed_seconds  REAL,
    app_version      TEXT,
    app_build_tag    TEXT
);
CREATE INDEX IF NOT EXISTS idx_proposals_owner   ON proposals(owner_id);
CREATE INDEX IF NOT EXISTS idx_proposals_project ON proposals(project_id);
CREATE INDEX IF NOT EXISTS idx_proposals_ts      ON proposals(timestamp);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

_ENTRY_FIELDS = (
    "proposal_id", "version_number", "version_label", "timestamp",
    "timestamp_display", "project_id", "owner_id", "code_count",
    "page_count", "output_file", "output_name", "file_size_bytes",
    "sha256", "elapsed_seconds", "app_version", "app_build_tag",
)


def _entry_to_row(entry: dict[str, Any]) -> tuple | None:
    """حوّل سجل JSON إلى صف إدخال — يُرجع None إن كان السجل تالفاً."""
    try:
        pid = str(entry["proposal_id"])
        codes = entry.get("codes", [])
        if not pid or not isinstance(codes, list):
            return None
        row = [
            pid,
            int(entry.get("version_number", 0)),
            str(entry.get("version_label", "")),
            str(entry.get("timestamp", "")),
            str(entry.get("timestamp_display", "")),
            str(entry.get("project_id", "")),
            str(entry.get("owner_id", "")),
            json.dumps(codes, ensure_ascii=False),
            int(entry.get("code_count", len(codes))),
            int(entry.get("page_count", 0)),
            str(entry.get("output_file", "")),
            str(entry.get("output_name", "")),
            int(entry.get("file_size_bytes", 0)),
            str(entry.get("sha256", "")),
            float(entry.get("elapsed_seconds", 0.0)),
            str(entry.get("app_version", "")),
            str(entry.get("app_build_tag", "")),
        ]
        return tuple(row)
    except (KeyError, TypeError, ValueError):
        return None


def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    entry = {field: row[field] for field in _ENTRY_FIELDS}
    try:
        entry["codes"] = json.loads(row["codes_json"])
    except (ValueError, TypeError):
        entry["codes"] = []
    return entry


class ArchiveIndex:
    """فهرس SQLite محلي لسجل العروض — بحث وإحصاء سريع."""

    def __init__(self, db_path: str | Path = _DEFAULT_DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Connection / schema
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            conn = sqlite3.connect(str(self._db_path), timeout=5.0)
            conn.row_factory = sqlite3.Row
            # T004: وصول متزامن آمن — WAL يسمح بالقراءة أثناء الكتابة
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._conn = conn
        return self._conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        conn.executescript(_SCHEMA_SQL)
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        if current < _SCHEMA_VERSION:
            conn.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
        conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "ArchiveIndex":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def add_entry(self, entry: dict[str, Any]) -> bool:
        """أدرج/حدّث سجلاً واحداً. يُرجع False للسجل التالف."""
        row = _entry_to_row(entry)
        if row is None:
            logger.warning("ArchiveIndex: skipped malformed entry %r", entry.get("proposal_id"))
            return False
        conn = self._connect()
        placeholders = ", ".join("?" for _ in row)
        conn.execute(
            f"INSERT OR REPLACE INTO proposals VALUES ({placeholders})", row
        )
        conn.commit()
        return True

    def update_path(self, proposal_id: str, new_path: str) -> bool:
        """حدّث مسار ملف المخرج بعد نقله (FR-007)."""
        conn = self._connect()
        cur = conn.execute(
            "UPDATE proposals SET output_file=? WHERE proposal_id=?",
            (str(new_path), str(proposal_id)),
        )
        conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def count(self) -> int:
        conn = self._connect()
        return conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]

    def search(
        self,
        query: str = "",
        owner_id: str = "",
        project_id: str = "",
        limit: int = 300,
    ) -> list[dict[str, Any]]:
        """بحث اقتراني حر عبر (المعرف، اسم الملف، الجهة، المشروع، الأكواد، الوسم)."""
        conn = self._connect()
        where: list[str] = []
        params: list[Any] = []

        q = (query or "").strip()
        if q:
            like = f"%{q}%"
            where.append(
                "(proposal_id LIKE ? OR output_name LIKE ? OR owner_id LIKE ? "
                "OR project_id LIKE ? OR codes_json LIKE ? OR version_label LIKE ?)"
            )
            params.extend([like] * 6)
        if owner_id:
            where.append("owner_id = ?")
            params.append(owner_id)
        if project_id:
            where.append("project_id = ?")
            params.append(project_id)

        sql = "SELECT * FROM proposals"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(int(limit))

        rows = conn.execute(sql, params).fetchall()
        return [_row_to_entry(r) for r in rows]

    # ------------------------------------------------------------------
    # Rebuild from JSON (T020/T021)
    # ------------------------------------------------------------------

    @staticmethod
    def _json_source_hash(json_path: Path) -> str:
        try:
            return hashlib.sha256(
                Path(json_path).read_bytes()
            ).hexdigest()
        except OSError:
            return ""

    def source_up_to_date(self, json_path: str | Path = _DEFAULT_JSON_PATH) -> bool:
        """هل الفهرس مبني من النسخة الحالية من JSON؟"""
        conn = self._connect()
        row = conn.execute(
            "SELECT value FROM meta WHERE key='source_sha256'"
        ).fetchone()
        stored = row["value"] if row else ""
        current = self._json_source_hash(Path(json_path))
        return bool(stored) and stored == current

    def mark_source_synced(self, json_path: str | Path = _DEFAULT_JSON_PATH) -> None:
        """سجّل أن الفهرس متزامن مع نسخة JSON الحالية (بعد إضافة مفردة)."""
        conn = self._connect()
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('source_sha256', ?)",
            (self._json_source_hash(Path(json_path)),),
        )
        conn.commit()

    def rebuild_from_json(
        self, json_path: str | Path = _DEFAULT_JSON_PATH
    ) -> tuple[int, int]:
        """أعد بناء الفهرس كلياً من JSON — (المضافة، المتخطاة التالفة).

        تنفيذ جملي واحد (executemany) — آلاف السجلات في أجزاء من الثانية.
        """
        json_path = Path(json_path)
        added = skipped = 0
        rows: list[tuple] = []
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            entries = data.get("proposal_versions", []) if isinstance(data, dict) else []
        except (OSError, ValueError):
            logger.warning("ArchiveIndex: unreadable source %s", json_path)
            entries = []

        for entry in entries:
            if not isinstance(entry, dict):
                skipped += 1
                continue
            row = _entry_to_row(entry)
            if row is None:
                skipped += 1
                continue
            rows.append(row)

        conn = self._connect()
        placeholders = ", ".join("?" for _ in range(len(_ENTRY_FIELDS) + 1))
        with conn:
            conn.execute("DELETE FROM proposals")
            if rows:
                conn.executemany(
                    f"INSERT OR REPLACE INTO proposals VALUES ({placeholders})", rows
                )
            added = len(rows)
            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES('source_sha256', ?)",
                (self._json_source_hash(json_path),),
            )
        if skipped:
            logger.info(
                "ArchiveIndex: rebuild skipped %d malformed records from %s",
                skipped, json_path.name,
            )
        return added, skipped

    def ensure_built(self, json_path: str | Path = _DEFAULT_JSON_PATH) -> tuple[str, int, int]:
        """اضمن جاهزية الفهرس: أعد البناء إن كان المصدر تغيّر أو الفهرس فارغاً.

        Returns:
            ("fresh" | "rebuilt", added, skipped)
        """
        json_path = Path(json_path)
        empty_source = not json_path.exists()
        if empty_source:
            return "fresh", 0, 0
        if self.count() == 0 or not self.source_up_to_date(json_path):
            added, skipped = self.rebuild_from_json(json_path)
            return "rebuilt", added, skipped
        return "fresh", 0, 0

    # ------------------------------------------------------------------
    # Insights (US3)
    # ------------------------------------------------------------------

    def insights(self) -> dict[str, Any]:
        """رؤى تجميعية: أكثر الجهات، النشاط الشهري، المتوسطات."""
        conn = self._connect()
        total = self.count()

        top_owners = [
            (r["owner_id"], r["n"])
            for r in conn.execute(
                "SELECT owner_id, COUNT(*) AS n FROM proposals "
                "GROUP BY owner_id ORDER BY n DESC LIMIT 5"
            ).fetchall()
        ]

        monthly = [
            {
                "month": r["month"],
                "count": r["n"],
                "avg_pages": round(r["avg_pages"] or 0.0, 1),
            }
            for r in conn.execute(
                "SELECT substr(timestamp, 1, 7) AS month, COUNT(*) AS n, "
                "AVG(page_count) AS avg_pages FROM proposals "
                "WHERE timestamp != '' GROUP BY month ORDER BY month DESC LIMIT 12"
            ).fetchall()
        ]

        avg_row = conn.execute(
            "SELECT AVG(code_count) AS ac, AVG(page_count) AS ap FROM proposals"
        ).fetchone()

        return {
            "total": total,
            "top_owners": top_owners,
            "monthly": monthly,
            "avg_codes": round(avg_row["ac"] or 0.0, 1),
            "avg_pages": round(avg_row["ap"] or 0.0, 1),
        }
