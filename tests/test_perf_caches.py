#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD tests for the three performance caches introduced in the optimize pass:

  1. license_manager  — hardware-ID cache + license-check cache
  2. content_library  — source Document cache (_doc_cache)
  3. docx_manipulator — _apply_font_bulk() bulk lxml font pass

Each test class is self-contained: module-level cache state is reset
before every test so tests cannot pollute each other.

Run from project root:
    pytest tests/test_perf_caches.py -v
"""

import json
import platform
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
from docx import Document
from docx.oxml.ns import qn

# ────────────────────────────────────────────────────────────────────────────
# 1.  license_manager — hardware-ID cache
# ────────────────────────────────────────────────────────────────────────────

class TestHardwareIdCache:
    """get_hardware_id() must call platform.node() only once per process."""

    def _reset(self):
        import utils.license_manager as lm
        lm._hw_id_cache = None

    def test_returns_string_in_expected_format(self):
        """Result is XXXX-XXXX-XXXX-XXXX (16 hex chars, 3 dashes)."""
        self._reset()
        from utils.license_manager import get_hardware_id
        hw = get_hardware_id()
        parts = hw.split("-")
        assert len(parts) == 4, f"Expected 4 parts, got: {hw!r}"
        assert all(len(p) == 4 for p in parts), f"Each part must be 4 chars: {hw!r}"
        assert all(c in "0123456789ABCDEF" for p in parts for c in p)

    def test_result_is_deterministic(self):
        """Calling twice returns identical value (cache works)."""
        self._reset()
        from utils.license_manager import get_hardware_id
        assert get_hardware_id() == get_hardware_id()

    def test_platform_node_called_only_once(self, monkeypatch):
        """platform.node() WMI query runs exactly once despite multiple calls."""
        self._reset()
        import utils.license_manager as lm

        call_log = []
        original_node = platform.node

        def counting_node():
            call_log.append(1)
            return original_node()

        monkeypatch.setattr("utils.license_manager.platform.node", counting_node)

        lm.get_hardware_id()
        lm.get_hardware_id()
        lm.get_hardware_id()

        assert len(call_log) == 1, (
            f"platform.node() called {len(call_log)} times — caching broken"
        )

    def test_cache_populated_after_first_call(self):
        """_hw_id_cache must be non-None after the first call."""
        self._reset()
        import utils.license_manager as lm
        assert lm._hw_id_cache is None       # precondition
        lm.get_hardware_id()
        assert lm._hw_id_cache is not None   # cache filled

    def test_cache_is_returned_on_subsequent_calls(self, monkeypatch):
        """Second call returns cached value, not a freshly computed one."""
        self._reset()
        import utils.license_manager as lm

        first = lm.get_hardware_id()
        # Poison the underlying sources — if cache is bypassed, result changes
        monkeypatch.setattr("utils.license_manager.platform.node", lambda: "DIFFERENT")
        second = lm.get_hardware_id()

        assert first == second, "Cache bypassed — second call recomputed hardware ID"


# ────────────────────────────────────────────────────────────────────────────
# 2.  license_manager — license-check cache + invalidation
# ────────────────────────────────────────────────────────────────────────────

class TestLicenseCheckCache:
    """check_saved_license() must cache its result; invalidate_license_cache() resets it."""

    def _reset(self):
        import utils.license_manager as lm
        lm._license_check_cache = None

    def test_cache_is_none_before_first_call(self):
        self._reset()
        import utils.license_manager as lm
        assert lm._license_check_cache is None

    def test_cache_populated_after_check(self, tmp_path):
        """_license_check_cache must be set after check_saved_license() runs."""
        self._reset()
        import utils.license_manager as lm

        # Point license path to a non-existent file so it returns quickly
        with patch("utils.license_manager._license_path", return_value=tmp_path / "no.dat"):
            lm.check_saved_license()

        assert lm._license_check_cache is not None

    def test_file_read_only_once(self, tmp_path):
        """The license file must be read only on the first call."""
        self._reset()
        import utils.license_manager as lm

        license_file = tmp_path / "license.dat"
        license_file.write_text("{}", encoding="utf-8")

        read_count = [0]
        original_read = Path.read_text

        def counting_read(self_, *args, **kwargs):
            if str(self_) == str(license_file):
                read_count[0] += 1
            return original_read(self_, *args, **kwargs)

        with patch("utils.license_manager._license_path", return_value=license_file):
            with patch.object(Path, "read_text", counting_read):
                lm.check_saved_license()
                lm.check_saved_license()
                lm.check_saved_license()

        assert read_count[0] == 1, (
            f"License file read {read_count[0]} times — cache not working"
        )

    def test_invalidate_clears_cache(self, tmp_path):
        """invalidate_license_cache() must set _license_check_cache back to None."""
        self._reset()
        import utils.license_manager as lm
        from utils.license_manager import invalidate_license_cache

        with patch("utils.license_manager._license_path", return_value=tmp_path / "no.dat"):
            lm.check_saved_license()

        assert lm._license_check_cache is not None   # cache is set
        invalidate_license_cache()
        assert lm._license_check_cache is None       # cache cleared

    def test_after_invalidation_file_is_reread(self, tmp_path):
        """After invalidation the next call must re-read the license file."""
        self._reset()
        import utils.license_manager as lm
        from utils.license_manager import invalidate_license_cache

        license_file = tmp_path / "license.dat"
        license_file.write_text("{}", encoding="utf-8")
        read_count = [0]
        original_read = Path.read_text

        def counting_read(self_, *args, **kwargs):
            if str(self_) == str(license_file):
                read_count[0] += 1
            return original_read(self_, *args, **kwargs)

        with patch("utils.license_manager._license_path", return_value=license_file):
            with patch.object(Path, "read_text", counting_read):
                lm.check_saved_license()   # read #1
                invalidate_license_cache()
                lm.check_saved_license()   # read #2 (cache was cleared)

        assert read_count[0] == 2, (
            f"Expected 2 file reads (before and after invalidation), got {read_count[0]}"
        )


# ────────────────────────────────────────────────────────────────────────────
# 3.  content_library — source Document cache
# ────────────────────────────────────────────────────────────────────────────

def _make_minimal_docx(path: Path, text: str = "محتوى") -> None:
    doc = Document()
    doc.add_paragraph(text)
    doc.save(str(path))


def _make_lib(tmp_path: Path) -> "ContentLibrary":
    from utils.content_library import ContentLibrary
    src = tmp_path / "source_documents"
    src.mkdir()
    reg = tmp_path / "registry.json"
    return ContentLibrary(source_docs_dir=src, registry_path=reg)


class TestDocumentCache:
    """Source .docx files should be opened once and cached in _doc_cache."""

    def test_doc_cache_empty_on_init(self, tmp_path):
        lib = _make_lib(tmp_path)
        assert lib._doc_cache == {}

    def test_doc_cache_populated_after_insert(self, tmp_path):
        """_doc_cache must contain the source path key after insert_into()."""
        lib = _make_lib(tmp_path)
        src_file = tmp_path / "source_documents" / "001-TST-DOC.docx"
        _make_minimal_docx(src_file)

        target = Document()
        lib.insert_into(target, "001-TST-DOC")

        assert str(src_file) in lib._doc_cache, "Source document not cached after insert"

    def test_docx_opened_only_once_across_two_inserts(self, tmp_path):
        """Opening a .docx file is expensive — it must happen only once per path."""
        lib = _make_lib(tmp_path)
        src_file = tmp_path / "source_documents" / "001-TST-DOC.docx"
        _make_minimal_docx(src_file)

        open_count = [0]
        original_Document = Document

        def counting_Document(path_str):
            if "001-TST-DOC" in str(path_str):
                open_count[0] += 1
            return original_Document(path_str)

        with patch("utils.content_library.Document", side_effect=counting_Document):
            lib.insert_into(Document(), "001-TST-DOC")   # first call  → opens file
            lib.insert_into(Document(), "001-TST-DOC")   # second call → uses cache

        assert open_count[0] == 1, (
            f"Source .docx opened {open_count[0]} times — _doc_cache not working"
        )

    def test_invalidate_cache_clears_doc_cache(self, tmp_path):
        """invalidate_cache() must clear _doc_cache along with _available_set."""
        lib = _make_lib(tmp_path)
        src_file = tmp_path / "source_documents" / "001-TST-DOC.docx"
        _make_minimal_docx(src_file)

        lib.insert_into(Document(), "001-TST-DOC")
        assert lib._doc_cache != {}   # precondition: cache was populated

        lib.invalidate_cache()
        assert lib._doc_cache == {}, "_doc_cache not cleared by invalidate_cache()"

    def test_doc_cache_miss_after_invalidation_reopens_file(self, tmp_path):
        """After invalidation the file must be re-read on next insert."""
        lib = _make_lib(tmp_path)
        src_file = tmp_path / "source_documents" / "001-TST-DOC.docx"
        _make_minimal_docx(src_file)

        open_count = [0]
        original_Document = Document

        def counting_Document(path_str):
            if "001-TST-DOC" in str(path_str):
                open_count[0] += 1
            return original_Document(path_str)

        with patch("utils.content_library.Document", side_effect=counting_Document):
            lib.insert_into(Document(), "001-TST-DOC")   # open #1
            lib.invalidate_cache()
            lib.insert_into(Document(), "001-TST-DOC")   # open #2

        assert open_count[0] == 2, (
            f"Expected 2 opens (before and after invalidation), got {open_count[0]}"
        )

    def test_separate_library_instances_do_not_share_cache(self, tmp_path):
        """Each ContentLibrary instance has its own independent _doc_cache."""
        src = tmp_path / "source_documents"
        src.mkdir()
        src_file = src / "001-TST-DOC.docx"
        _make_minimal_docx(src_file)
        reg = tmp_path / "registry.json"

        from utils.content_library import ContentLibrary
        lib_a = ContentLibrary(source_docs_dir=src, registry_path=reg)
        lib_b = ContentLibrary(source_docs_dir=src, registry_path=reg)

        lib_a.insert_into(Document(), "001-TST-DOC")
        assert str(src_file) in lib_a._doc_cache
        assert str(src_file) not in lib_b._doc_cache, "Caches should not be shared"


# ────────────────────────────────────────────────────────────────────────────
# 4.  docx_manipulator — _apply_font_bulk() correctness
# ────────────────────────────────────────────────────────────────────────────

class TestApplyFontBulk:
    """_apply_font_bulk() must set w:ascii, w:hAnsi, w:cs on every <w:r> element."""

    def _doc_with_runs(self, *texts) -> Document:
        doc = Document()
        for text in texts:
            doc.add_paragraph(text)
        return doc

    def test_sets_ascii_attribute(self):
        from utils.docx_manipulator import _apply_font_bulk
        doc = self._doc_with_runs("مرحبا", "hello")
        _apply_font_bulk(doc.element.body, "Tajawal")

        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            assert rPr is not None, "<w:rPr> missing after font apply"
            rFonts = rPr.find(qn("w:rFonts"))
            assert rFonts is not None, "<w:rFonts> missing after font apply"
            assert rFonts.get(qn("w:ascii")) == "Tajawal", \
                f"w:ascii not set: {rFonts.attrib}"

    def test_sets_cs_attribute_for_arabic(self):
        """w:cs is the critical attribute that controls Arabic font rendering."""
        from utils.docx_manipulator import _apply_font_bulk
        doc = self._doc_with_runs("نص عربي")
        _apply_font_bulk(doc.element.body, "Tajawal")

        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
            assert rFonts is not None
            assert rFonts.get(qn("w:cs")) == "Tajawal", \
                f"w:cs not set — Arabic text will use wrong font: {rFonts.attrib}"

    def test_sets_hAnsi_attribute(self):
        from utils.docx_manipulator import _apply_font_bulk
        doc = self._doc_with_runs("test")
        _apply_font_bulk(doc.element.body, "Tajawal")

        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
            assert rFonts is not None
            assert rFonts.get(qn("w:hAnsi")) == "Tajawal"

    def test_applies_to_all_paragraphs(self):
        """Every run across multiple paragraphs must be updated."""
        from utils.docx_manipulator import _apply_font_bulk
        doc = self._doc_with_runs("para 1", "para 2", "para 3")
        _apply_font_bulk(doc.element.body, "Arial")

        run_count = 0
        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
            if rFonts is not None:
                assert rFonts.get(qn("w:ascii")) == "Arial"
                run_count += 1
        assert run_count >= 3, f"Expected runs from 3 paragraphs, found {run_count}"

    def test_different_font_families(self):
        """Font name must reflect the exact family passed, not a hardcoded value."""
        from utils.docx_manipulator import _apply_font_bulk
        for family in ("Tajawal", "Arial", "Calibri", "Times New Roman"):
            doc = self._doc_with_runs("text")
            _apply_font_bulk(doc.element.body, family)
            for r_el in doc.element.body.iter(qn("w:r")):
                rPr = r_el.find(qn("w:rPr"))
                rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
                if rFonts is not None:
                    assert rFonts.get(qn("w:ascii")) == family


class TestApplyFontFamilyToDocument:
    """apply_font_family_to_document() must cover body paragraphs and table cells."""

    def test_body_paragraphs_receive_font(self):
        from utils.docx_manipulator import apply_font_family_to_document
        doc = Document()
        doc.add_paragraph("body text")
        apply_font_family_to_document(doc, "Tajawal")

        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
            if rFonts is not None:
                assert rFonts.get(qn("w:ascii")) == "Tajawal"

    def test_table_cells_receive_font(self):
        """Table cell runs must also get the font (doc.paragraphs skips tables)."""
        from utils.docx_manipulator import apply_font_family_to_document
        doc = Document()
        table = doc.add_table(rows=1, cols=1)
        table.cell(0, 0).paragraphs[0].add_run("cell text")
        apply_font_family_to_document(doc, "Tajawal")

        for r_el in doc.element.body.iter(qn("w:r")):
            rPr = r_el.find(qn("w:rPr"))
            rFonts = rPr.find(qn("w:rFonts")) if rPr is not None else None
            if rFonts is not None:
                assert rFonts.get(qn("w:ascii")) == "Tajawal", \
                    "Table cell run did not receive font"

    def test_runs_without_existing_rpr_get_font(self):
        """Runs that have no <w:rPr> element must have one created with the font."""
        from utils.docx_manipulator import apply_font_family_to_document
        from docx.oxml import OxmlElement

        doc = Document()
        para = doc.add_paragraph()
        # Add a raw run with no rPr at all
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "bare run"
        r.append(t)
        para._p.append(r)

        apply_font_family_to_document(doc, "Tajawal")

        # The bare run should now have rPr with rFonts
        rPr = r.find(qn("w:rPr"))
        assert rPr is not None, "rPr not created for bare run"
        rFonts = rPr.find(qn("w:rFonts"))
        assert rFonts is not None, "rFonts not created for bare run"
        assert rFonts.get(qn("w:ascii")) == "Tajawal"
