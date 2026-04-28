#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for utils/pdf_exporter.py — mocked to avoid needing Word installed."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.pdf_exporter import export_to_pdf, is_pdf_export_available


# ── export_to_pdf ──────────────────────────────────────────────────────────


def test_returns_pdf_path_on_success(tmp_path):
    """Returns a .pdf Path when docx2pdf.convert() succeeds."""
    docx = tmp_path / "proposal.docx"
    docx.write_bytes(b"fake docx content")
    pdf = tmp_path / "proposal.pdf"

    def fake_convert(src, dst):
        Path(dst).write_bytes(b"fake pdf content")

    with patch("utils.pdf_exporter.convert", fake_convert, create=True):
        with patch("utils.pdf_exporter.export_to_pdf.__wrapped__", None, create=True):
            pass

    # Patch the import inside the function
    mock_convert = MagicMock(side_effect=lambda src, dst: Path(dst).write_bytes(b"%PDF"))
    with patch.dict("sys.modules", {"docx2pdf": MagicMock(convert=mock_convert)}):
        result = export_to_pdf(docx)

    assert result is not None
    assert result.suffix == ".pdf"
    assert result.stem == "proposal"
    assert result.parent == tmp_path


def test_returns_none_when_source_missing(tmp_path):
    """Returns None immediately if the .docx file does not exist."""
    missing = tmp_path / "nonexistent.docx"
    result = export_to_pdf(missing)
    assert result is None


def test_returns_none_when_docx2pdf_not_installed(tmp_path):
    """Returns None gracefully when docx2pdf is not installed."""
    docx = tmp_path / "proposal.docx"
    docx.write_bytes(b"fake docx")

    with patch.dict("sys.modules", {"docx2pdf": None}):
        result = export_to_pdf(docx)

    assert result is None


def test_returns_none_when_convert_raises(tmp_path):
    """Returns None when docx2pdf.convert() raises an exception."""
    docx = tmp_path / "proposal.docx"
    docx.write_bytes(b"fake docx")

    mock_convert = MagicMock(side_effect=RuntimeError("Word not found"))
    with patch.dict("sys.modules", {"docx2pdf": MagicMock(convert=mock_convert)}):
        result = export_to_pdf(docx)

    assert result is None


def test_pdf_saved_same_directory_as_docx(tmp_path):
    """PDF is saved alongside the .docx, not in a different folder."""
    docx = tmp_path / "sub" / "proposal.docx"
    docx.parent.mkdir()
    docx.write_bytes(b"fake docx")

    mock_convert = MagicMock(
        side_effect=lambda src, dst: Path(dst).write_bytes(b"%PDF")
    )
    with patch.dict("sys.modules", {"docx2pdf": MagicMock(convert=mock_convert)}):
        result = export_to_pdf(docx)

    assert result is not None
    assert result.parent == tmp_path / "sub"


def test_accepts_string_path(tmp_path):
    """export_to_pdf accepts a str path, not only Path objects."""
    docx = tmp_path / "proposal.docx"
    docx.write_bytes(b"fake docx")

    mock_convert = MagicMock(
        side_effect=lambda src, dst: Path(dst).write_bytes(b"%PDF")
    )
    with patch.dict("sys.modules", {"docx2pdf": MagicMock(convert=mock_convert)}):
        result = export_to_pdf(str(docx))   # pass str, not Path

    assert result is not None


# ── is_pdf_export_available ────────────────────────────────────────────────


def test_available_when_docx2pdf_installed():
    """Returns True when docx2pdf can be imported."""
    with patch.dict("sys.modules", {"docx2pdf": MagicMock()}):
        assert is_pdf_export_available() is True


def test_not_available_when_docx2pdf_missing():
    """Returns False when docx2pdf is not installed."""
    with patch.dict("sys.modules", {"docx2pdf": None}):
        assert is_pdf_export_available() is False
