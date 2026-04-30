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
            _copy_docx_body(source_path, target_doc)
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

def _copy_docx_body(source_path: Path, target_doc: Document) -> None:
    """
    Deep-copy all body elements from source .docx into target_doc,
    re-mapping image relationships so embedded images are preserved.
    """
    from docx.opc.part import Part
    from docx.opc.packuri import PackURI

    source = Document(str(source_path))
    target_body = target_doc.element.body
    target_part = target_doc.part

    # Build a map of image relationships in source.
    # Each image gets a unique partname (counter-based) to prevent collisions
    # when multiple source files contain images named image1.png, image2.png…
    image_map: Dict[str, str] = {}
    _img_counter = 0
    for rel_id, rel in source.part.rels.items():
        if "image" not in rel.reltype:
            continue
        try:
            image_data = rel.target_part.blob
            content_type = rel.target_part.content_type
            # Normalise extension
            ext = content_type.split("/")[-1].lower()
            if ext == "jpeg":
                ext = "jpg"
            elif ext == "x-emf":
                ext = "emf"
            elif ext == "x-wmf":
                ext = "wmf"

            # Unique partname — avoids collisions across multiple source files
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

    # Deep-copy body elements (paragraphs, tables, etc.)
    for element in source.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag == "sectPr":
            continue  # skip section properties — keep target's layout
        node = deepcopy(element)
        # Remap image rIds in the copied node
        if image_map:
            _remap_image_ids(node, image_map)
        target_body.append(node)


def _remap_image_ids(node: Any, image_map: Dict[str, str]) -> None:
    """Update r:embed and r:id attributes in blip/image elements."""
    blip_tag = qn("a:blip")
    embed_attr = qn("r:embed")
    link_attr = qn("r:link")
    for el in node.iter():
        for attr in (embed_attr, link_attr):
            old_id = el.get(attr)
            if old_id and old_id in image_map:
                el.set(attr, image_map[old_id])
