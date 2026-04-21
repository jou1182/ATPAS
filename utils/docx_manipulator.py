#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph


# ---------------------------------------------------------------------------
# Open / Save
# ---------------------------------------------------------------------------

def open_docx(path: str | Path) -> Document:
    """Open a .docx file and return a Document object."""
    return Document(str(path))


def save_docx(doc: Document, path: str | Path) -> None:
    """Save a Document, creating parent directories as needed."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest))


def new_docx() -> Document:
    """Return a blank Document."""
    return Document()


# ---------------------------------------------------------------------------
# Paragraph extraction
# ---------------------------------------------------------------------------

def get_paragraphs(doc: Document) -> List[Paragraph]:
    """Return all paragraphs in document body order."""
    return list(doc.paragraphs)


def extract_sections(doc: Document) -> List[Dict]:
    """
    Parse the document into a list of section dicts:
        {"heading": str, "level": int, "paragraphs": [str], "style": str}

    Heading paragraphs (Heading 1/2/3) start a new section.
    Non-heading paragraphs accumulate into the current section.
    """
    sections: List[Dict] = []
    current: Optional[Dict] = None

    for para in doc.paragraphs:
        style_name = para.style.name if para.style else "Normal"
        text = para.text.strip()

        if style_name.startswith("Heading"):
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1
            current = {"heading": text, "level": level, "paragraphs": [], "style": style_name}
            sections.append(current)
        else:
            if current is None:
                current = {"heading": "", "level": 0, "paragraphs": [], "style": "Normal"}
                sections.append(current)
            if text:
                current["paragraphs"].append(text)

    return sections


# ---------------------------------------------------------------------------
# Style utilities
# ---------------------------------------------------------------------------

def set_paragraph_font(
    para: Paragraph,
    family: str,
    size_pt: float,
    bold: bool = False,
    italic: bool = False,
    color_hex: Optional[str] = None,
) -> None:
    """Apply font properties to every run in a paragraph."""
    for run in para.runs:
        run.font.name = family
        run.font.size = Pt(size_pt)
        run.bold = bold
        run.italic = italic
        if color_hex:
            r, g, b = _hex_to_rgb(color_hex)
            run.font.color.rgb = RGBColor(r, g, b)


def set_rtl(para: Paragraph) -> None:
    """Enable right-to-left direction on a paragraph."""
    pPr = para._p.get_or_add_pPr()
    bidi = pPr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        pPr.append(bidi)
    bidi.set(qn("w:val"), "1")


def clear_document(doc: Document) -> None:
    """Remove all paragraphs and tables from a document body."""
    from docx.oxml.ns import qn as _qn
    body = doc.element.body
    for child in list(body):
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag in ("p", "tbl"):
            body.remove(child)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert '#RRGGBB' to (R, G, B) integers."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
