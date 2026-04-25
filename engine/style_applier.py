#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Applies owner-specific visual style (header, footer, colors, compliance matrix,
heritage clause) to a Document using the JSON style templates.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph

from utils.json_manager import load_json

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_STYLE_DIR = _PROJECT_ROOT / "templates" / "style_templates"


class StyleApplier:
    """
    Load an owner's style template and apply it to a Document.

    Usage:
        applier = StyleApplier()
        applier.apply_style(doc, "nwc")
    """

    def __init__(self, style_dir: str | Path = _STYLE_DIR):
        self._style_dir = Path(style_dir)
        self._cache: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_style(self, doc: Document, owner_id: str) -> None:
        """Apply all owner-specific styles to the document."""
        spec = self._load_spec(owner_id)
        if not spec:
            logger.warning("No style spec found for owner '%s' — using defaults", owner_id)
            return

        self._apply_margins(doc, spec)
        self._apply_header(doc, spec)
        self._apply_footer(doc, spec)

        # Owner-specific extras
        if spec.get("heritage_clause", {}).get("enabled"):
            self._add_heritage_clause(doc, spec)
        if spec.get("compliance_matrix", {}).get("enabled"):
            self._add_compliance_matrix(doc, spec)

        logger.info("Applied '%s' style to document", owner_id)

    def get_primary_color(self, owner_id: str) -> Optional[str]:
        """Return the primary hex color for the owner's theme."""
        spec = self._load_spec(owner_id)
        return spec.get("colors", {}).get("primary") if spec else None

    # ------------------------------------------------------------------
    # Margin
    # ------------------------------------------------------------------

    def _apply_margins(self, doc: Document, spec: Dict) -> None:
        margins = spec.get("margins_cm", {})
        from docx.shared import Cm
        for section in doc.sections:
            if "top" in margins:
                section.top_margin = Cm(margins["top"])
            if "bottom" in margins:
                section.bottom_margin = Cm(margins["bottom"])
            if "left" in margins:
                section.left_margin = Cm(margins["left"])
            if "right" in margins:
                section.right_margin = Cm(margins["right"])

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def _apply_header(self, doc: Document, spec: Dict) -> None:
        hdr_spec = spec.get("header", {})
        if not hdr_spec.get("enabled"):
            return
        for section in doc.sections:
            section.different_first_page_header_footer = False
            header = section.header
            header.is_linked_to_previous = False
            for para in header.paragraphs:
                para.clear()
            if not header.paragraphs:
                header.add_paragraph()
            para = header.paragraphs[0]
            run = para.add_run(hdr_spec.get("text_ar", ""))
            run.font.size = Pt(10)
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if hdr_spec.get("line_below"):
                _add_bottom_border(para)

    def _apply_footer(self, doc: Document, spec: Dict) -> None:
        ftr_spec = spec.get("footer", {})
        if not ftr_spec.get("enabled"):
            return
        for section in doc.sections:
            footer = section.footer
            footer.is_linked_to_previous = False
            for para in footer.paragraphs:
                para.clear()
            if not footer.paragraphs:
                footer.add_paragraph()
            para = footer.paragraphs[0]

            text = ftr_spec.get("text_ar", "")
            if ftr_spec.get("show_page_number"):
                run = para.add_run(text + "  ")
                run.font.size = Pt(9)
                _add_page_number(para)
            else:
                run = para.add_run(text)
                run.font.size = Pt(9)

            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if ftr_spec.get("line_above"):
                _add_top_border(para)

    # ------------------------------------------------------------------
    # Owner-specific extras
    # ------------------------------------------------------------------

    def _add_heritage_clause(self, doc: Document, spec: Dict) -> None:
        hc = spec.get("heritage_clause", {})
        title = hc.get("title_ar", "بند الحفاظ على التراث")
        text = spec.get("specific_requirements", {}).get(
            "heritage_clause_text",
            "يلتزم المقاول بالحفاظ على التراث العمراني.",
        )
        # Insert after introduction — for now append before body content
        # (builder.py will call this at the right insertion point)
        doc.add_heading(title, level=2)
        doc.add_paragraph(text)

    def _add_compliance_matrix(self, doc: Document, spec: Dict) -> None:
        cm = spec.get("compliance_matrix", {})
        title = cm.get("title_ar", "مصفوفة الامتثال")
        doc.add_page_break()
        doc.add_heading(title, level=1)
        doc.add_paragraph("يتضمن هذا الملحق جدول الامتثال الكامل للمتطلبات.")

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------

    def _load_spec(self, owner_id: str) -> Optional[Dict]:
        if owner_id in self._cache:
            return self._cache[owner_id]
        path = self._style_dir / f"{owner_id}_style.json"
        if not path.exists():
            return None
        try:
            spec = load_json(path)
            self._cache[owner_id] = spec
            return spec
        except Exception as exc:
            logger.error("Failed to load style for '%s': %s", owner_id, exc)
            return None


# ---------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------

def _add_page_number(para: Paragraph) -> None:
    """Insert an automatic PAGE field into para."""
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = " PAGE "
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")

    run = para.add_run()
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def _add_bottom_border(para: Paragraph) -> None:
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "auto")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_top_border(para: Paragraph) -> None:
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "single")
    top.set(qn("w:sz"), "6")
    top.set(qn("w:space"), "1")
    top.set(qn("w:color"), "auto")
    pBdr.append(top)
    pPr.append(pBdr)
