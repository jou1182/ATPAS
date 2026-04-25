#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Content Import Tool — اداة استيراد المحتوى

Splits a master Word document into per-code content files, or registers
individual files with code IDs.

Usage examples:
    # Split a master document by Heading 1 (each heading = one code)
    python tools/import_content.py split master.docx --output-dir templates/source_documents/

    # Register an existing file with a code ID
    python tools/import_content.py register 001-SUR-BASE "C:/my_files/survey.docx"

    # List all codes that have content files available
    python tools/import_content.py list

    # Show which codes are missing content files
    python tools/import_content.py missing

    # Preview what would be split (dry run)
    python tools/import_content.py split master.docx --dry-run
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from docx import Document
from docx.oxml.ns import qn

from utils.content_library import ContentLibrary
from utils.json_manager import load_json, save_json

_REGISTRY_PATH = Path("codes_registry.json")
_OUTPUT_DIR = Path("templates/source_documents")


# ---------------------------------------------------------------------------
# Split command
# ---------------------------------------------------------------------------

def cmd_split(args) -> None:
    """Split a master .docx into individual code files by Heading 1."""
    master_path = Path(args.master)
    if not master_path.exists():
        print(f"ERROR: File not found: {master_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    doc = Document(str(master_path))
    sections = _split_by_heading(doc)

    if not sections:
        print("No Heading 1 sections found. Make sure your document uses 'Heading 1' style.")
        sys.exit(1)

    print(f"Found {len(sections)} sections:")
    for heading, paragraphs in sections:
        code_id = _extract_code_from_heading(heading)
        status = "(code found)" if code_id else "(no code detected)"
        print(f"  • {heading[:60]:<60}  {status}")

    if args.dry_run:
        print("\nDry run — no files written.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    created = 0
    lib = ContentLibrary(output_dir)

    for heading, paragraphs in sections:
        code_id = _extract_code_from_heading(heading)
        if not code_id:
            safe_name = _safe_filename(heading)
            print(f"  SKIP (no code): {heading[:50]} — save manually as {safe_name}.docx")
            continue

        out_path = output_dir / f"{code_id}.docx"
        _write_section(heading, paragraphs, out_path)
        print(f"  ✓ {code_id} → {out_path}")
        created += 1

    print(f"\nDone: {created}/{len(sections)} files created in {output_dir}")


# ---------------------------------------------------------------------------
# Register command
# ---------------------------------------------------------------------------

def cmd_register(args) -> None:
    lib = ContentLibrary()
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    lib.register(args.code_id, file_path)
    print(f"Registered: {args.code_id} → {file_path}")


# ---------------------------------------------------------------------------
# List command
# ---------------------------------------------------------------------------

def cmd_list(args) -> None:
    lib = ContentLibrary()
    available = lib.list_available()
    if not available:
        print("No content files registered yet.")
        print(f"Drop .docx files into {_OUTPUT_DIR}/ or run 'import_content.py split'")
        return
    print(f"Available content files ({len(available)}):")
    for code_id in available:
        path = lib.find(code_id)
        print(f"  {code_id:<25}  {path}")


# ---------------------------------------------------------------------------
# Missing command
# ---------------------------------------------------------------------------

def cmd_missing(args) -> None:
    if not _REGISTRY_PATH.exists():
        print(f"ERROR: codes_registry.json not found.")
        sys.exit(1)

    registry = load_json(_REGISTRY_PATH)
    codes = registry.get("codes", {})
    lib = ContentLibrary()

    missing = [c for c in codes if not lib.exists(c) and codes[c].get("status") == "active"]
    if not missing:
        print("All active codes have content files. ")
        return

    print(f"Missing content files ({len(missing)} codes):")
    for code_id in missing:
        code = codes[code_id]
        print(f"  {code_id:<25}  {code.get('activity_name_ar', '')}")

    print(f"\nTip: Create these files in {_OUTPUT_DIR}/")
    print(f"     Or run: python tools/import_content.py split your_master.docx")


# ---------------------------------------------------------------------------
# Splitting helpers
# ---------------------------------------------------------------------------

def _split_by_heading(doc: Document) -> List[Tuple[str, list]]:
    """
    Split document into (heading_text, [elements]) pairs at each Heading 1.
    Returns list of (heading, body_elements) tuples.
    """
    sections: List[Tuple[str, list]] = []
    current_heading: Optional[str] = None
    current_elements: list = []

    for element in doc.element.body:
        # Check if this is a Heading 1 paragraph
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag == "p":
            para = _para_from_element(element, doc)
            if para and para.style and para.style.name == "Heading 1":
                if current_heading is not None:
                    sections.append((current_heading, current_elements))
                current_heading = para.text.strip()
                current_elements = []
                continue

        if current_heading is not None:
            current_elements.append(element)

    if current_heading is not None:
        sections.append((current_heading, current_elements))

    return sections


def _para_from_element(element, doc: Document):
    """Try to get a Paragraph object from an lxml element."""
    try:
        from docx.text.paragraph import Paragraph as DocxPara
        from docx.oxml.text.paragraph import CT_P
        if isinstance(element, CT_P):
            return DocxPara(element, doc)
    except Exception:
        pass
    return None


def _extract_code_from_heading(heading: str) -> Optional[str]:
    """
    Extract a code ID from a heading string.
    Matches patterns like: 001-SUR-BASE, MY-CUSTOM-001, PIPE-INSTALL-2
    Returns None if no pattern found.
    """
    import re
    # Match pattern: word chars and hyphens, at least one hyphen, starts with 3 digits OR word
    patterns = [
        r'\b(\d{3}-[A-Z]{2,5}-[A-Z0-9]{2,6})\b',   # 001-SUR-BASE style
        r'\b([A-Z]{2,10}-[A-Z0-9]{2,10}-[A-Z0-9]{2,10})\b',  # MY-CUSTOM-CODE style
        r'\b([A-Z0-9]{3,6}-[A-Z0-9]{2,8})\b',  # SHORT-CODE style
    ]
    for pattern in patterns:
        m = re.search(pattern, heading.upper())
        if m:
            return m.group(1)
    return None


def _safe_filename(text: str) -> str:
    """Convert arbitrary text to a safe filename."""
    import re
    return re.sub(r'[^\w\-]', '_', text)[:50]


def _write_section(heading: str, elements: list, output_path: Path) -> None:
    """Write a section (heading + body elements) to a new .docx file."""
    new_doc = Document()
    # Add the heading
    new_doc.add_heading(heading, level=1)
    # Deep-copy body elements
    target_body = new_doc.element.body
    for el in elements:
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "sectPr":
            continue
        target_body.append(deepcopy(el))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    new_doc.save(str(output_path))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ATPAS Content Import Tool — إدارة مكتبة محتوى البنود",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # split
    p_split = sub.add_parser("split", help="Split a master .docx into per-code files")
    p_split.add_argument("master", help="Path to master Word document")
    p_split.add_argument("--output-dir", default=str(_OUTPUT_DIR), help="Output directory")
    p_split.add_argument("--dry-run", action="store_true", help="Preview only, no files written")
    p_split.set_defaults(func=cmd_split)

    # register
    p_reg = sub.add_parser("register", help="Register a file path for a code ID")
    p_reg.add_argument("code_id", help="Activity code (e.g. 001-SUR-BASE)")
    p_reg.add_argument("file_path", help="Path to the .docx file")
    p_reg.set_defaults(func=cmd_register)

    # list
    p_list = sub.add_parser("list", help="List all available content files")
    p_list.set_defaults(func=cmd_list)

    # missing
    p_miss = sub.add_parser("missing", help="Show codes with no content file yet")
    p_miss.set_defaults(func=cmd_missing)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
