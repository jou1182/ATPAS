#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for engine/parser.py.

Tests cover: cache hit/miss, force re-parse, missing file error,
get_section_by_code, _file_hash determinism, and _annotate_images distribution.

Run from the project root:
    python -m pytest tests/test_parser.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document

from engine.parser import Parser, _annotate_images, _file_hash


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_docx(path: Path, text: str = "Sample paragraph") -> Path:
    """Create a minimal .docx file at *path* and return it."""
    doc = Document()
    doc.add_paragraph(text)
    doc.save(str(path))
    return path


# ---------------------------------------------------------------------------
# Parser.__init__
# ---------------------------------------------------------------------------

class TestParserInit:
    def test_creates_cache_dir(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "cache_output"
        Parser(cache_dir=cache_dir)
        assert cache_dir.exists()

    def test_cache_file_in_output_dir(self, tmp_path: Path) -> None:
        p = Parser(cache_dir=tmp_path)
        assert p._cache_path.parent == tmp_path

    def test_cache_starts_empty_on_fresh_dir(self, tmp_path: Path) -> None:
        p = Parser(cache_dir=tmp_path)
        assert isinstance(p._cache, dict)


# ---------------------------------------------------------------------------
# Parser.parse_document — error cases
# ---------------------------------------------------------------------------

class TestParseDocumentErrors:
    def test_raises_file_not_found_on_missing_docx(self, tmp_path: Path) -> None:
        p = Parser(cache_dir=tmp_path)
        with pytest.raises(FileNotFoundError, match="not found"):
            p.parse_document(tmp_path / "nonexistent.docx", tmp_path / "out")

    def test_output_dir_created_automatically(self, tmp_path: Path) -> None:
        docx = _make_docx(tmp_path / "source.docx")
        out_dir = tmp_path / "nested" / "output"
        p = Parser(cache_dir=tmp_path)
        p.parse_document(docx, out_dir)
        assert out_dir.exists()


# ---------------------------------------------------------------------------
# Parser.parse_document — cache behaviour
# ---------------------------------------------------------------------------

class TestParseDocumentCache:
    def test_returns_list_of_dicts(self, tmp_path: Path) -> None:
        docx = _make_docx(tmp_path / "doc.docx")
        p = Parser(cache_dir=tmp_path)
        result = p.parse_document(docx, tmp_path / "out")
        assert isinstance(result, list)

    def test_sections_json_written_to_output_dir(self, tmp_path: Path) -> None:
        docx = _make_docx(tmp_path / "doc.docx")
        out_dir = tmp_path / "out"
        p = Parser(cache_dir=tmp_path)
        p.parse_document(docx, out_dir)
        assert (out_dir / "sections.json").exists()

    def test_second_call_hits_cache(self, tmp_path: Path) -> None:
        """Parse the same file twice — second call must return same result from cache."""
        docx = _make_docx(tmp_path / "doc.docx", text="Cache test content")
        out_dir = tmp_path / "out"
        p = Parser(cache_dir=tmp_path)

        result1 = p.parse_document(docx, out_dir)
        result2 = p.parse_document(docx, out_dir)
        assert result1 == result2

    def test_force_true_bypasses_cache(self, tmp_path: Path) -> None:
        """force=True must re-parse even when cache entry exists."""
        docx = _make_docx(tmp_path / "doc.docx")
        out_dir = tmp_path / "out"
        p = Parser(cache_dir=tmp_path)

        # Prime the cache
        p.parse_document(docx, out_dir)
        # Force re-parse — should not raise and should return a list
        result = p.parse_document(docx, out_dir, force=True)
        assert isinstance(result, list)

    def test_cache_updated_after_parse(self, tmp_path: Path) -> None:
        docx = _make_docx(tmp_path / "doc.docx")
        p = Parser(cache_dir=tmp_path)
        assert str(docx) not in p._cache     # not yet parsed
        p.parse_document(docx, tmp_path / "out")
        assert str(docx) in p._cache          # now cached


# ---------------------------------------------------------------------------
# Parser.get_section_by_code
# ---------------------------------------------------------------------------

class TestGetSectionByCode:
    _sections = [
        {"heading": "001-SUR-BASE — الأعمال التحضيرية", "body": "..."},
        {"heading": "002-EXC-FINE — حفر ناعم", "body": "..."},
        {"heading": "003-PIP-SEW — مواسير صرف", "body": "..."},
    ]

    def test_finds_matching_section(self) -> None:
        p = Parser.__new__(Parser)   # bypass __init__ for unit test
        result = p.get_section_by_code(self._sections, "002-EXC-FINE")
        assert result is not None
        assert "002-EXC-FINE" in result["heading"]

    def test_returns_none_when_code_not_found(self) -> None:
        p = Parser.__new__(Parser)
        result = p.get_section_by_code(self._sections, "999-XXX-ZZZ")
        assert result is None

    def test_returns_none_on_empty_sections(self) -> None:
        p = Parser.__new__(Parser)
        result = p.get_section_by_code([], "001-SUR-BASE")
        assert result is None

    def test_returns_first_match(self) -> None:
        """When multiple sections match, the first is returned."""
        sections = [
            {"heading": "001-SUR-BASE — version A"},
            {"heading": "001-SUR-BASE — version B"},
        ]
        p = Parser.__new__(Parser)
        result = p.get_section_by_code(sections, "001-SUR-BASE")
        assert "version A" in result["heading"]


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------

class TestFileHash:
    def test_same_file_same_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "file.bin"
        f.write_bytes(b"deterministic content")
        h1 = _file_hash(f)
        h2 = _file_hash(f)
        assert h1 == h2

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.bin"
        f2 = tmp_path / "b.bin"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert _file_hash(f1) != _file_hash(f2)

    def test_returns_64_char_hex_string(self, tmp_path: Path) -> None:
        f = tmp_path / "hash_test.bin"
        f.write_bytes(b"any bytes")
        h = _file_hash(f)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_empty_file_has_consistent_hash(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        h1 = _file_hash(f)
        h2 = _file_hash(f)
        assert h1 == h2


# ---------------------------------------------------------------------------
# _annotate_images
# ---------------------------------------------------------------------------

class TestAnnotateImages:
    def test_empty_image_list_leaves_sections_unchanged(self) -> None:
        sections = [{"heading": "A"}, {"heading": "B"}]
        _annotate_images(sections, [])
        for s in sections:
            assert s.get("images") == []

    def test_images_distributed_round_robin(self, tmp_path: Path) -> None:
        sections = [{"heading": "A"}, {"heading": "B"}]
        imgs = [Path(f"img{i}.png") for i in range(4)]
        _annotate_images(sections, imgs)
        # 4 images, 2 sections → each gets 2
        assert len(sections[0]["images"]) == 2
        assert len(sections[1]["images"]) == 2

    def test_more_images_than_sections(self, tmp_path: Path) -> None:
        sections = [{"heading": "only"}]
        imgs = [Path(f"img{i}.png") for i in range(5)]
        _annotate_images(sections, imgs)
        assert len(sections[0]["images"]) == 5

    def test_more_sections_than_images(self) -> None:
        sections = [{"heading": "A"}, {"heading": "B"}, {"heading": "C"}]
        imgs = [Path("img0.png")]
        _annotate_images(sections, imgs)
        # Only first section gets image
        assert len(sections[0]["images"]) == 1
        assert len(sections[1]["images"]) == 0
        assert len(sections[2]["images"]) == 0

    def test_no_sections_no_crash(self) -> None:
        _annotate_images([], [Path("img.png")])   # must not raise

    def test_images_stored_as_strings(self) -> None:
        sections = [{"heading": "A"}]
        _annotate_images(sections, [Path("some/path/img.png")])
        assert isinstance(sections[0]["images"][0], str)
