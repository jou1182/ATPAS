#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the archive index (specs/004) — search, dual-write, rebuild, perf.

Run:
    python -m pytest tests/test_archive_index.py -v
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _entry(pid: str, i: int = 0, owner: str = "nwc", project: str = "wastewater") -> dict:
    return {
        "proposal_id": pid,
        "version_number": i + 1,
        "version_label": f"PV-{i + 1:06d}",
        "timestamp": f"2026-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T10:00:00",
        "timestamp_display": "2026-08-25  10:00",
        "project_id": project,
        "owner_id": owner,
        "codes": ["001-SUR-BASE", f"003-PIP-{i:03d}"],
        "code_count": 2,
        "page_count": 30 + (i % 50),
        "output_file": rf"C:\out\{pid}.docx",
        "output_name": f"{pid}.docx",
        "file_size_bytes": 1000 + i,
        "sha256": f"hash-{pid}",
        "elapsed_seconds": 0.4,
        "app_version": "3.2",
        "app_build_tag": "3.2.20260825",
    }


# ── Core schema + CRUD ───────────────────────────────────────────────────────

class TestArchiveIndexBasics:
    def test_wal_mode_enabled(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        mode = idx._connect().execute("PRAGMA journal_mode").fetchone()[0]
        assert str(mode).lower() == "wal"

    def test_add_and_search_by_code(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        assert idx.add_entry(_entry("A1", 0))   # codes تحتوي 003-PIP-000
        assert idx.add_entry(_entry("A2", 1, owner="swa"))  # تحتوي 003-PIP-001
        assert idx.count() == 2

        hits = idx.search(query="003-PIP-001")
        assert len(hits) == 1 and hits[0]["proposal_id"] == "A2"

        hits = idx.search(query="003-PIP-000")
        assert len(hits) == 1 and hits[0]["proposal_id"] == "A1"

    def test_search_filters_owner_project(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.add_entry(_entry("A1", 0, owner="nwc", project="wastewater"))
        idx.add_entry(_entry("A2", 1, owner="swa", project="water_supply"))
        assert len(idx.search(owner_id="swa")) == 1
        assert len(idx.search(project_id="wastewater")) == 1
        assert len(idx.search(owner_id="nwc", project_id="water_supply")) == 0

    def test_malformed_entry_rejected(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        assert idx.add_entry({"bad": True}) is False
        assert idx.count() == 0

    def test_update_path(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.add_entry(_entry("A1"))
        assert idx.update_path("A1", r"D:\moved\A1.docx") is True
        assert idx.search(query="A1")[0]["output_file"] == r"D:\moved\A1.docx"
        assert idx.update_path("ghost", "x") is False

    def test_search_ordering_newest_first(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.add_entry(_entry("OLD", 0))   # 2026-01
        idx.add_entry(_entry("NEW", 11))  # 2026-12
        hits = idx.search()
        assert hits[0]["proposal_id"] == "NEW"


# ── Dual write (FR-004 / SC-004) ─────────────────────────────────────────────

class TestDualWrite:
    def test_save_entry_writes_json_and_index(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "version.json").write_text("{}", encoding="utf-8")
        out = tmp_path / "p.docx"
        out.write_bytes(b"doc")

        from utils.proposal_versions import ProposalVersionManager
        from utils.archive_index import ArchiveIndex

        mgr = ProposalVersionManager(
            json_path=tmp_path / "pv.json",
            csv_path=tmp_path / "pv.csv",
            version_path=tmp_path / "version.json",
        )
        entry = mgr.save_entry(
            project_id="wastewater",
            owner_id="nwc",
            codes=["001-SUR-BASE"],
            output_file=out,
            elapsed_seconds=0.5,
            page_count=40,
        )

        idx = ArchiveIndex(tmp_path / "archive_index.db")
        assert idx.count() == 1
        hits = idx.search(query=entry["proposal_id"])
        assert len(hits) == 1
        assert hits[0]["codes"] == ["001-SUR-BASE"]
        assert idx.source_up_to_date(tmp_path / "pv.json")

    def test_index_failure_does_not_break_registry(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "version.json").write_text("{}", encoding="utf-8")
        out = tmp_path / "p.docx"
        out.write_bytes(b"doc")

        from utils.proposal_versions import ProposalVersionManager
        import utils.proposal_versions as pv_module

        # اجعل فتح الفهرس يفشل — يجب أن يستمر تسجيل JSON
        monkeypatch.setattr(
            "utils.archive_index.ArchiveIndex.__init__",
            lambda self, db_path=None: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        mgr = ProposalVersionManager(
            json_path=tmp_path / "pv.json",
            csv_path=tmp_path / "pv.csv",
            version_path=tmp_path / "version.json",
        )
        entry = mgr.save_entry(
            project_id="wastewater", owner_id="nwc", codes=[],
            output_file=out, elapsed_seconds=0.1, page_count=1,
        )
        assert entry["proposal_id"]  # JSON سُجل رغم فشل الفهرس


# ── Rebuild / migration (US2) ────────────────────────────────────────────────

class TestRebuild:
    def _write_json(self, tmp_path, entries):
        src = tmp_path / "pv.json"
        src.write_text(
            json.dumps({"proposal_versions": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        return src

    def test_rebuild_counts_and_skips_corrupt(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        src = self._write_json(tmp_path, [
            _entry("GOOD1", 0),
            {"broken": True},                 # تالف: بلا معرف
            _entry("GOOD2", 1),
            "not-a-dict",                     # تالف: نوع خاطئ
        ])
        idx = ArchiveIndex(tmp_path / "idx.db")
        added, skipped = idx.rebuild_from_json(src)
        assert (added, skipped) == (2, 2)
        assert idx.count() == 2
        assert idx.source_up_to_date(src)

    def test_rebuild_replaces_stale_rows(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.add_entry(_entry("STALE", 0))
        src = self._write_json(tmp_path, [_entry("FRESH", 1)])
        idx.rebuild_from_json(src)
        assert idx.count() == 1
        assert idx.search()[0]["proposal_id"] == "FRESH"

    def test_ensure_built_triggers_on_source_change(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        src = self._write_json(tmp_path, [_entry("A1", 0)])
        idx = ArchiveIndex(tmp_path / "idx.db")

        status, added, _ = idx.ensure_built(src)
        assert status == "rebuilt" and added == 1

        status, _, _ = idx.ensure_built(src)
        assert status == "fresh"          # لا إعادة بناء بلا تغيير

        self._write_json(tmp_path, [_entry("A1", 0), _entry("A2", 1)])
        status, added, _ = idx.ensure_built(src)
        assert status == "rebuilt" and added == 2

    def test_full_match_json_vs_index(self, tmp_path):
        """SC-002: تطابق 1:1 بعد البناء التلقائي."""
        from utils.archive_index import ArchiveIndex
        entries = [_entry(f"P{i:03d}", i, owner=f"o{i % 3}") for i in range(50)]
        src = self._write_json(tmp_path, entries)
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.ensure_built(src)
        assert idx.count() == len(entries)
        ids_index = {r["proposal_id"] for r in idx.search(limit=1000)}
        ids_json = {e["proposal_id"] for e in entries}
        assert ids_index == ids_json

    def test_missing_source_is_fresh_empty(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        status, added, skipped = idx.ensure_built(tmp_path / "ghost.json")
        assert (status, added, skipped) == ("fresh", 0, 0)


# ── Performance (SC-001 / SC-003) ────────────────────────────────────────────

class TestPerformance:
    def _bulk_json(self, tmp_path, n: int) -> Path:
        entries = [_entry(f"B{i:06d}", i, owner=f"o{i % 20}", project=f"p{i % 6}") for i in range(n)]
        src = tmp_path / "big.json"
        src.write_text(
            json.dumps({"proposal_versions": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        return src

    def test_search_5000_under_500ms(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        src = self._bulk_json(tmp_path, 5000)
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.rebuild_from_json(src)

        t0 = time.perf_counter()
        hits = idx.search(query="B000499")
        free = time.perf_counter() - t0
        assert len(hits) == 1
        assert free < 0.5, f"free search took {free * 1000:.0f}ms"

        t0 = time.perf_counter()
        hits = idx.search(owner_id="o7", project_id="p3")
        filt = time.perf_counter() - t0
        assert hits
        assert filt < 0.5, f"filtered search took {filt * 1000:.0f}ms"

    def test_rebuild_20000_fast_and_complete(self, tmp_path):
        """SC-003: 20000 سجل ببناء سريع وكامل (تنفيذ الخلفية في الحوار)."""
        from utils.archive_index import ArchiveIndex
        src = self._bulk_json(tmp_path, 20000)
        idx = ArchiveIndex(tmp_path / "idx.db")
        t0 = time.perf_counter()
        added, skipped = idx.rebuild_from_json(src)
        elapsed = time.perf_counter() - t0
        assert added == 20000 and skipped == 0
        assert elapsed < 30, f"bulk rebuild took {elapsed:.1f}s"
        assert idx.count() == 20000


# ── Insights (US3 / T032) ────────────────────────────────────────────────────

class TestInsights:
    def test_insights_math_matches_manual(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        # شهران حقيقيان ثابتان: أغسطس ×3 و يوليو ×1 — طوابع زمنية صريحة
        stamps = ("2026-08-01T10:00:00", "2026-08-10T10:00:00",
                  "2026-08-20T10:00:00", "2026-07-05T10:00:00")
        owners = ("nwc", "nwc", "swa", "mot")
        pages = (40, 50, 60, 20)
        entries = []
        for i, (ts, owner, p) in enumerate(zip(stamps, owners, pages)):
            e = _entry(f"T{i}", i, owner=owner)
            e["timestamp"] = ts
            e["page_count"] = p
            entries.append(e)

        src = tmp_path / "pv.json"
        src.write_text(
            json.dumps({"proposal_versions": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        idx = ArchiveIndex(tmp_path / "idx.db")
        idx.rebuild_from_json(src)

        ins = idx.insights()
        assert ins["total"] == 4
        assert ins["top_owners"][0] == ("nwc", 2)

        by_month = {m["month"]: m for m in ins["monthly"]}
        assert by_month["2026-08"]["count"] == 3
        assert by_month["2026-08"]["avg_pages"] == 50.0   # (40+50+60)/3
        assert by_month["2026-07"]["count"] == 1
        assert by_month["2026-07"]["avg_pages"] == 20.0
        assert ins["avg_pages"] == round((40 + 50 + 60 + 20) / 4, 1)

    def test_insights_empty_index(self, tmp_path):
        from utils.archive_index import ArchiveIndex
        idx = ArchiveIndex(tmp_path / "idx.db")
        ins = idx.insights()
        assert ins == {
            "total": 0, "top_owners": [], "monthly": [],
            "avg_codes": 0.0, "avg_pages": 0.0,
        }


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# ── UI integration (index mode dialog) ───────────────────────────────────────

class TestArchiveDialogIndexMode:
    """ProposalArchiveDialog in index mode: cards render, insights toggle works."""

    def _make_dialog(self, qapp, tmp_path, monkeypatch, n=3):
        from PyQt5.QtWidgets import QDialog
        monkeypatch.chdir(tmp_path)
        (tmp_path / "version.json").write_text("{}", encoding="utf-8")
        out = tmp_path / "p.docx"
        out.write_bytes(b"doc")

        from utils.proposal_versions import ProposalVersionManager
        mgr = ProposalVersionManager(
            json_path=tmp_path / "pv.json",
            csv_path=tmp_path / "pv.csv",
            version_path=tmp_path / "version.json",
        )
        for i in range(n):
            mgr.save_entry(
                project_id="wastewater" if i % 2 == 0 else "water_supply",
                owner_id="nwc" if i % 2 == 0 else "swa",
                codes=[f"00{i}-X-{i:03d}"],
                output_file=out,
                elapsed_seconds=0.3,
                page_count=30 + i,
            )

        from ui.build_history import BuildHistoryManager
        from ui.proposal_archive_dialog import ProposalArchiveDialog
        dlg = ProposalArchiveDialog(
            manager=BuildHistoryManager(tmp_path / "bh.json"),
            versions_manager=mgr,
        )
        return dlg, mgr

    def test_index_mode_renders_all_entries(self, qapp, tmp_path, monkeypatch):
        dlg, mgr = self._make_dialog(qapp, tmp_path, monkeypatch, n=3)
        try:
            assert dlg._index is not None
            assert dlg._index.count() == 3
            # البطاقات المرسومة = 3 (وضع الفهرس يتجاوز حد الـ50 للسجل السريع)
            cards = [
                w for w in dlg._scroll_widget.findChildren(type(dlg._scroll_widget))
                if w.metaObject().className() == "QFrame"
            ]
            assert dlg._count_badge.text().startswith("3")
        finally:
            dlg.close()

    def test_insights_toggle_shows_summary(self, qapp, tmp_path, monkeypatch):
        dlg, mgr = self._make_dialog(qapp, tmp_path, monkeypatch, n=3)
        try:
            dlg._toggle_insights()
            assert not dlg._insights_lbl.isHidden()
            assert "الإجمالي: 3" in dlg._insights_lbl.text()
            dlg._toggle_insights()
            assert dlg._insights_lbl.isHidden()
        finally:
            dlg.close()

    def test_search_via_index_filters(self, qapp, tmp_path, monkeypatch):
        dlg, mgr = self._make_dialog(qapp, tmp_path, monkeypatch, n=4)
        try:
            dlg._search_edit.setText("nwc")
            # nwc entries: i%2==0 → 2 من 4
            assert "من 4" in dlg._status_lbl.text()
        finally:
            dlg.close()

    def test_legacy_mode_without_versions_manager(self, qapp, tmp_path):
        from ui.build_history import BuildHistoryManager
        from ui.proposal_archive_dialog import ProposalArchiveDialog
        mgr = BuildHistoryManager(tmp_path / "bh.json")
        mgr.save_entry(
            project_id="asphalt",
            owner_id="mot",
            codes=["001-SUR-BASE"],
            output_file="",
            elapsed_seconds=0.2,
            page_count=10,
        )
        dlg = ProposalArchiveDialog(manager=mgr)  # بلا versions_manager
        try:
            assert dlg._index is None            # السلوك القديم محفوظ
            assert dlg._count_badge.text().startswith("1")
        finally:
            dlg.close()
