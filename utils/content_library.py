#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Content Library Manager — maps activity codes to their source Word documents.

Rules (checked in order):
  1. Explicit override in content_registry.json: {"006-INS-VALVE": "path/to/file.docx"}
  2. Exact name match: templates/source_documents/{code_id}.docx
  3. Case-insensitive / hyphen-tolerant scan of source_documents/
  4. None → builder uses metadata placeholder

Adding a new activity to the library:
  - Drop {code_id}.docx into templates/source_documents/   (zero config)
  - OR register a path in content_registry.json            (any name, any folder)
"""

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.json_manager import save_json

from docx import Document
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SOURCE_DOCS_DIR = _PROJECT_ROOT / "templates" / "source_documents"
_CONTENT_REGISTRY = _PROJECT_ROOT / "templates" / "content_registry.json"


class ContentLibrary:
    """
    Manages the mapping between activity codes and their source .docx files.

    Usage:
        lib = ContentLibrary()
        path = lib.find("001-SUR-BASE")          # → Path or None
        lib.insert_into(doc, "001-SUR-BASE")      # copies content into doc
        lib.register("MY-CODE", "my_file.docx")  # manual registration
    """

    def __init__(
        self,
        source_docs_dir: str | Path = _SOURCE_DOCS_DIR,
        registry_path: str | Path = _CONTENT_REGISTRY,
    ):
        self._source_dir = Path(source_docs_dir)
        self._registry_path = Path(registry_path)
        self._registry: Dict[str, str] = self._load_registry()
        # Availability cache — built once on first exists() call, invalidated on write
        self._available_set: Optional[set] = None
        # Parsed Document cache — each source .docx is opened once per session.
        # _copy_docx_body only READS from the source Document (all mutations go
        # to the target), so reusing the same object across calls is safe.
        self._doc_cache: Dict[str, "Document"] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find(self, code_id: str) -> Optional[Path]:
        """
        Return the Path to the source .docx for code_id, or None if not found.
        Lookup order: registry → exact name → fuzzy scan.
        """
        # 1. Explicit registry entry
        if code_id in self._registry:
            path = Path(self._registry[code_id])
            if not path.is_absolute():
                path = self._source_dir / path
            if path.exists():
                return path
            logger.warning("Registry entry for %s points to missing file: %s", code_id, path)

        # 2. Exact file name
        exact = self._source_dir / f"{code_id}.docx"
        if exact.exists():
            return exact

        # 3. Case-insensitive scan only (hyphens kept — prevents wrong-file matches)
        for f in self._source_dir.glob("*.docx"):
            if f.stem.lower() == code_id.lower():
                if f.stem != code_id:
                    logger.warning(
                        "Content for %s served from %s (case mismatch)", code_id, f.name
                    )
                return f

        return None

    def exists(self, code_id: str) -> bool:
        """Return True if a source file exists for code_id.

        Checks both:
          - exact match (file named exactly code_id.docx), and
          - fuzzy/normalized match (hyphen/case-insensitive, same as find()).

        This ensures exists() is always consistent with find() — if find()
        returns a path, exists() must return True for the same code_id.
        """
        available = self._get_available_set()
        return code_id in available or code_id.lower() in available

    def _get_available_set(self) -> set:
        if self._available_set is None:
            self._available_set = self._build_available_set()
        return self._available_set

    def _build_available_set(self) -> set:
        """Scan registry + source_docs dir once and cache the result."""
        result: set = set()
        # From explicit registry entries (only those pointing to real files)
        for code_id, path_str in self._registry.items():
            p = Path(path_str)
            if not p.is_absolute():
                p = self._source_dir / p
            if p.exists():
                result.add(code_id)
        # From files named {code_id}.docx (exact and case-insensitive only)
        try:
            for f in self._source_dir.glob("*.docx"):
                result.add(f.stem)
                result.add(f.stem.lower())   # case-insensitive fallback only
        except OSError:
            pass
        return result

    def invalidate_cache(self) -> None:
        """Discard the availability cache. Call after adding/removing files."""
        self._available_set = None
        self._doc_cache.clear()

    def list_available(self) -> List[str]:
        """Return all code_ids that have content files available."""
        from_registry = list(self._registry.keys())
        from_files = [f.stem for f in self._source_dir.glob("*.docx")]
        return sorted(set(from_registry + from_files))

    def insert_into(self, target_doc: Document, code_id: str) -> bool:
        """
        Copy all content from the source .docx for code_id into target_doc.

        Returns True if content was inserted, False if no source found
        (caller should fall back to placeholder).

        Content is inserted via deep XML copy — preserves text, formatting,
        tables, and inline images (image binaries are re-embedded).
        """
        source_path = self.find(code_id)
        if source_path is None:
            return False

        try:
            _copy_docx_body(source_path, target_doc, self._doc_cache)
            logger.debug("Inserted content for %s from %s", code_id, source_path)
            return True
        except Exception as exc:
            logger.error("Failed to insert content for %s: %s", code_id, exc)
            return False

    def register(self, code_id: str, file_path: str | Path, save: bool = True) -> None:
        """
        Manually register a file path for a code_id.
        If save=True, persists the change to content_registry.json.
        """
        self._registry[code_id] = str(file_path)
        self.invalidate_cache()
        if save:
            self._save_registry()
        logger.info("Registered content for %s → %s", code_id, file_path)

    def unregister(self, code_id: str, save: bool = True) -> None:
        if code_id in self._registry:
            del self._registry[code_id]
            self.invalidate_cache()
            if save:
                self._save_registry()

    # ------------------------------------------------------------------
    # Registry persistence
    # ------------------------------------------------------------------

    def _load_registry(self) -> Dict[str, str]:
        if not self._registry_path.exists():
            return {}
        try:
            with open(self._registry_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_registry(self) -> None:
        save_json(self._registry, self._registry_path)


# ---------------------------------------------------------------------------
# Deep XML copy — the engine that makes it all work
# ---------------------------------------------------------------------------

def _copy_docx_body(
    source_path: Path,
    target_doc: Document,
    doc_cache: Optional[Dict[str, "Document"]] = None,
) -> None:
    """
    Deep-copy all body elements from source .docx into target_doc,
    re-mapping image relationships and numbering definitions so that
    embedded images and numbered lists are fully preserved with RTL direction.

    doc_cache: optional dict keyed by str(source_path). When provided, parsed
    Document objects are reused across calls — opening a .docx file takes
    ~50-80ms on HDD, so caching yields a significant speedup when the same
    source file appears in multiple builds within the same session.
    """
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI

    cache_key = str(source_path)
    if doc_cache is not None and cache_key in doc_cache:
        source = doc_cache[cache_key]
    else:
        source = Document(str(source_path))
        if doc_cache is not None:
            doc_cache[cache_key] = source
    target_body = target_doc.element.body
    target_part = target_doc.part

    # ── 1. Image relationship mapping ────────────────────────────────────
    # Each image gets a unique partname to prevent collisions when multiple
    # source files contain images named image1.png, image2.png, etc.
    image_map: Dict[str, str] = {}
    _img_counter = 0
    for rel_id, rel in source.part.rels.items():
        if "image" not in rel.reltype:
            continue
        try:
            image_data = rel.target_part.blob
            content_type = rel.target_part.content_type
            ext = content_type.split("/")[-1].lower()
            if ext == "jpeg":
                ext = "jpg"
            elif ext == "x-emf":
                ext = "emf"
            elif ext == "x-wmf":
                ext = "wmf"

            _img_counter += 1
            unique_id = f"{abs(hash(source_path))}_{_img_counter}"
            new_partname = PackURI(f"/word/media/atpas_{unique_id}.{ext}")

            new_part = Part(new_partname, content_type, image_data)
            new_rel_id = target_part.relate_to(new_part, rel.reltype)
            image_map[rel_id] = new_rel_id
            logger.debug("Mapped image %s -> %s (%s)", rel_id, new_rel_id, new_partname)
        except Exception as exc:
            logger.warning(
                "Skipping image %s in %s — %s: %s",
                rel_id, source_path.name, type(exc).__name__, exc,
            )

    # ── 2. Numbering definitions — copy + RTL-patch ───────────────────────
    # Source paragraphs reference numIds defined in source's numbering.xml.
    # Without copying these definitions the target document has no record of
    # them, so Word falls back to generating default LTR numbered lists.
    # We copy every abstractNum/num, remap their IDs to avoid conflicts with
    # whatever the target already has, and patch each level to RTL layout:
    #   • lvlJc  "left"  → "right"
    #   • w:ind  w:left  → w:right  (indent from right margin, not left)
    num_id_map: Dict[str, str] = _copy_numbering_rtl(source, target_doc)

    # ── 3. Body elements — deep copy, insert before <w:sectPr> ───────────
    # python-docx's add_heading / add_paragraph inserts before sectPr.
    # Using lxml append() would place content after sectPr, breaking the
    # interleaved heading → content structure we rely on.
    sect_pr = target_body.find(qn("w:sectPr"))

    for element in source.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag == "sectPr":
            continue  # keep target's page layout, not source's
        node = deepcopy(element)
        if image_map:
            _remap_image_ids(node, image_map)
        if num_id_map:
            _remap_num_ids(node, num_id_map)
        if sect_pr is not None:
            sect_pr.addprevious(node)
        else:
            target_body.append(node)


# ---------------------------------------------------------------------------
# Numbering copy + RTL patch
# ---------------------------------------------------------------------------

def _copy_numbering_rtl(source: Document, target_doc: Document) -> Dict[str, str]:
    """
    Copy all abstractNum / num definitions from *source* into *target_doc*,
    patching each level for RTL layout, and return {old_numId → new_numId}.

    RTL patches per list level
    --------------------------
    * ``<w:lvlJc val="left">``  →  ``val="right"``
    * ``<w:ind w:left="X" …>``  →  ``<w:ind w:right="X" …>``
      (indentation measured from the **right** margin in RTL paragraphs)

    ID collision avoidance
    ----------------------
    The target document likely already has its own abstractNum / num
    definitions (python-docx ships a default template with numbering.xml).
    We compute the current maximum IDs and start our new entries above that
    ceiling, so there is no risk of clashing with pre-existing definitions.
    """
    # Source numbering part — bail early if absent
    try:
        src_num_part = source.part.numbering_part
    except AttributeError:
        src_num_part = None
    if src_num_part is None:
        return {}

    src_el = src_num_part._element  # <w:numbering>

    # Target numbering part — must exist (python-docx default template has one)
    try:
        tgt_num_part = target_doc.part.numbering_part
    except AttributeError:
        tgt_num_part = None
    if tgt_num_part is None:
        logger.warning("Target document has no numbering part — list numbering skipped")
        return {}

    tgt_el = tgt_num_part._element  # <w:numbering>

    # ── Compute safe starting IDs above current maxima ────────────────
    def _max_attr(parent, child_tag: str, attr: str) -> int:
        vals = []
        for el in parent.findall(qn(child_tag)):
            v = el.get(qn(attr))
            if v is not None:
                try:
                    vals.append(int(v))
                except ValueError:
                    pass
        return max(vals, default=-1)

    next_abs_id = _max_attr(tgt_el, "w:abstractNum", "w:abstractNumId") + 1
    next_num_id = _max_attr(tgt_el, "w:num",         "w:numId")         + 1

    # ── Copy abstractNums with new IDs + RTL patch ────────────────────
    abs_id_map: Dict[str, str] = {}
    for abs_num in src_el.findall(qn("w:abstractNum")):
        old_id = abs_num.get(qn("w:abstractNumId"))
        if old_id is None:
            continue
        new_id = str(next_abs_id)
        abs_id_map[old_id] = new_id
        next_abs_id += 1

        node = deepcopy(abs_num)
        node.set(qn("w:abstractNumId"), new_id)
        _patch_abstractnum_rtl(node)
        # abstractNums must precede nums in the XML
        first_num = tgt_el.find(qn("w:num"))
        if first_num is not None:
            first_num.addprevious(node)
        else:
            tgt_el.append(node)

    # ── Copy nums with new IDs, updating abstractNumId references ─────
    num_id_map: Dict[str, str] = {}
    for num in src_el.findall(qn("w:num")):
        old_id = num.get(qn("w:numId"))
        if old_id is None:
            continue
        new_id = str(next_num_id)
        num_id_map[old_id] = new_id
        next_num_id += 1

        node = deepcopy(num)
        node.set(qn("w:numId"), new_id)
        # Remap the abstractNumId reference inside this <w:num>
        abs_ref = node.find(qn("w:abstractNumId"))
        if abs_ref is not None:
            old_abs = abs_ref.get(qn("w:val"))
            if old_abs in abs_id_map:
                abs_ref.set(qn("w:val"), abs_id_map[old_abs])
        tgt_el.append(node)

    logger.debug(
        "Copied numbering from %s: %d abstractNums, %d nums",
        source.part.package.main_document_part.partname
        if hasattr(source.part, "package") else "source",
        len(abs_id_map), len(num_id_map),
    )
    return num_id_map


def _patch_abstractnum_rtl(abs_num) -> None:
    """Flip each list level in *abs_num* from LTR to RTL layout."""
    for lvl in abs_num.findall(qn("w:lvl")):
        # Justification: left → right
        lvl_jc = lvl.find(qn("w:lvlJc"))
        if lvl_jc is not None and lvl_jc.get(qn("w:val")) == "left":
            lvl_jc.set(qn("w:val"), "right")

        # Paragraph indent: swap w:left ↔ w:right so indentation is
        # measured from the right margin (RTL convention).
        pPr = lvl.find(qn("w:pPr"))
        if pPr is None:
            continue
        ind = pPr.find(qn("w:ind"))
        if ind is None:
            continue
        left_val  = ind.get(qn("w:left"))
        right_val = ind.get(qn("w:right"))
        if left_val is not None:
            ind.set(qn("w:right"), left_val)
            del ind.attrib[qn("w:left")]
        if right_val is not None:
            # Preserve what was the right value as left (for mixed docs)
            ind.set(qn("w:left"), right_val)


def _remap_num_ids(node: Any, num_id_map: Dict[str, str]) -> None:
    """Update every ``<w:numId val="…">`` in *node* with remapped IDs."""
    for num_id_el in node.iter(qn("w:numId")):
        old_val = num_id_el.get(qn("w:val"))
        if old_val and old_val in num_id_map:
            num_id_el.set(qn("w:val"), num_id_map[old_val])


def _remap_image_ids(node: Any, image_map: Dict[str, str]) -> None:
    """Update r:embed and r:id attributes in blip/image elements."""
    embed_attr = qn("r:embed")
    link_attr  = qn("r:link")
    for el in node.iter():
        for attr in (embed_attr, link_attr):
            old_id = el.get(attr)
            if old_id and old_id in image_map:
                el.set(attr, image_map[old_id])
