#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parses a source .docx template, extracts section data and images,
and caches results to avoid re-parsing unchanged files.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document

from utils.docx_manipulator import extract_sections
from utils.image_processor import extract_images
from utils.json_manager import load_json, save_json

logger = logging.getLogger(__name__)

_CACHE_FILENAME = ".parser_cache.json"


class Parser:
    """
    Parse a source Word document into sections + images.

    Usage:
        parser = Parser()
        sections = parser.parse_document("templates/source_documents/Master.docx", "output/extracted/")
    """

    def __init__(self, cache_dir: str | Path = "output"):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_path = self._cache_dir / _CACHE_FILENAME
        self._cache: Dict = self._load_cache()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_document(
        self,
        docx_path: str | Path,
        output_dir: str | Path,
        force: bool = False,
    ) -> List[Dict]:
        """
        Extract sections and images from docx_path.

        Results are saved to output_dir/sections.json and output_dir/images/.
        If the file has not changed since last parse (hash matches), the cached
        sections.json is returned unless force=True.

        Returns a list of section dicts (see docx_manipulator.extract_sections).
        """
        docx_path = Path(docx_path)
        out_dir = Path(output_dir)

        if not docx_path.exists():
            raise FileNotFoundError(f"Source document not found: {docx_path}")

        current_hash = _file_hash(docx_path)
        sections_path = out_dir / "sections.json"

        # Cache hit
        if (
            not force
            and sections_path.exists()
            and self._cache.get(str(docx_path)) == current_hash
        ):
            logger.info("Parser cache hit: %s", docx_path)
            return load_json(sections_path)

        logger.info("Parsing document: %s", docx_path)
        doc = Document(str(docx_path))

        # Extract section structure
        sections = extract_sections(doc)

        # Extract images
        images_dir = out_dir / "images"
        try:
            image_paths = extract_images(docx_path, images_dir)
            logger.info("Extracted %d images to %s", len(image_paths), images_dir)
        except Exception as exc:
            logger.warning("Image extraction failed (non-fatal): %s", exc)
            image_paths = []

        # Annotate sections with image references (by order)
        _annotate_images(sections, image_paths)

        # Save results
        out_dir.mkdir(parents=True, exist_ok=True)
        save_json(sections, sections_path)

        # Update cache
        self._cache[str(docx_path)] = current_hash
        self._save_cache()

        logger.info("Parsed %d sections from %s", len(sections), docx_path)
        return sections

    def get_section_by_code(
        self, sections: List[Dict], code_id: str
    ) -> Optional[Dict]:
        """Return the first section whose heading contains the code_id."""
        for s in sections:
            if code_id in s.get("heading", ""):
                return s
        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_cache(self) -> Dict:
        try:
            return load_json(self._cache_path, default={})
        except Exception:
            return {}

    def _save_cache(self) -> None:
        try:
            save_json(self._cache, self._cache_path)
        except Exception as exc:
            logger.warning("Could not save parser cache: %s", exc)


def _file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _annotate_images(sections: List[Dict], image_paths: List[Path]) -> None:
    """
    Distribute image paths across sections in document order.
    Each section gets a list of image path strings under the 'images' key.
    This is a best-effort heuristic; a future version can correlate by run index.
    """
    for s in sections:
        s.setdefault("images", [])
    if not image_paths:
        return
    # Round-robin distribution (rough heuristic until we can track run positions)
    for i, img in enumerate(image_paths):
        if sections:
            sections[i % len(sections)]["images"].append(str(img))
