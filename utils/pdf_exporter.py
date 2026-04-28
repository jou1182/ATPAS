#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PDF export utility for ATPAS.

Converts a generated .docx proposal to PDF using Microsoft Word (via docx2pdf).
Saves the PDF alongside the source .docx file with the same base name.

Usage:
    from utils.pdf_exporter import export_to_pdf

    pdf_path = export_to_pdf(Path("output/generated_documents/proposal.docx"))
    if pdf_path:
        print(f"PDF saved: {pdf_path}")
    else:
        print("Export failed — see logs")
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_to_pdf(docx_path: Path) -> Path | None:
    """Convert *docx_path* to PDF using Microsoft Word via docx2pdf.

    The PDF is saved in the same directory as the source .docx, with the
    same stem and a ``.pdf`` extension.

    Args:
        docx_path: Absolute or relative path to an existing ``.docx`` file.

    Returns:
        Path to the generated PDF on success, ``None`` on any failure.
    """
    docx_path = Path(docx_path)

    if not docx_path.exists():
        logger.error("PDF export failed — source file not found: %s", docx_path)
        return None

    pdf_path = docx_path.with_suffix(".pdf")

    try:
        from docx2pdf import convert  # type: ignore[import]
        convert(str(docx_path), str(pdf_path))
    except ImportError:
        logger.warning(
            "docx2pdf غير مثبت — قم بتشغيل: pip install docx2pdf"
        )
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("PDF export failed for %s: %s", docx_path, exc)
        return None

    if not pdf_path.exists():
        logger.error("PDF export ran but output not found: %s", pdf_path)
        return None

    logger.info("PDF exported successfully: %s", pdf_path)
    return pdf_path


def is_pdf_export_available() -> bool:
    """Return True if docx2pdf is installed and usable on this machine."""
    try:
        import docx2pdf  # type: ignore[import]  # noqa: F401
        return True
    except ImportError:
        return False
