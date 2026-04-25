#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import zipfile
from pathlib import Path
from typing import List, Optional

from PIL import Image as PILImage
from docx import Document
from docx.shared import Inches


_MIN_DPI = 300
_DEFAULT_MAX_WIDTH_INCHES = 6.0


def extract_images(docx_path: str | Path, output_dir: str | Path) -> List[Path]:
    """
    Extract all images from a .docx file to output_dir, preserving quality.

    Returns a list of saved image paths.
    Images that are below _MIN_DPI are saved as-is (not upscaled).
    """
    docx_path = Path(docx_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Path] = []

    # A .docx is a ZIP archive; images live under word/media/
    with zipfile.ZipFile(docx_path, "r") as z:
        for name in z.namelist():
            if not name.startswith("word/media/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".emf", ".wmf"}:
                continue

            data = z.read(name)
            filename = Path(name).name
            dest = out_dir / filename

            # For raster formats, check/preserve DPI metadata
            if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}:
                try:
                    with PILImage.open(io.BytesIO(data)) as img:
                        dpi = img.info.get("dpi", (72, 72))
                        # Save with at least _MIN_DPI in metadata if image is large enough
                        target_dpi = (max(dpi[0], _MIN_DPI), max(dpi[1], _MIN_DPI))
                        buf = io.BytesIO()
                        save_fmt = img.format or "PNG"
                        if save_fmt.upper() in {"JPEG", "JPG"}:
                            img.save(buf, format="JPEG", dpi=target_dpi, quality=95)
                        else:
                            img.save(buf, format="PNG", dpi=target_dpi)
                        dest.write_bytes(buf.getvalue())
                except Exception:
                    # Fall back to raw copy if Pillow can't handle it
                    dest.write_bytes(data)
            else:
                dest.write_bytes(data)

            saved.append(dest)

    return saved


def embed_image(
    doc: Document,
    image_path: str | Path,
    caption: str = "",
    max_width_inches: float = _DEFAULT_MAX_WIDTH_INCHES,
) -> None:
    """
    Add an image paragraph (+ optional caption) to the document.

    The image is scaled to fit within max_width_inches while preserving
    aspect ratio.  Caption is added as a separate paragraph with 'Caption'
    style (falls back to Normal if unavailable).
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Determine render width
    with PILImage.open(image_path) as img:
        w_px, h_px = img.size
        dpi = img.info.get("dpi", (96, 96))
        dpi_x = max(dpi[0], 1)
        natural_width_in = w_px / dpi_x
        render_width = min(natural_width_in, max_width_inches)

    para = doc.add_paragraph()
    run = para.add_run()
    run.add_picture(str(image_path), width=Inches(render_width))
    para.alignment = 1  # WD_ALIGN_PARAGRAPH.CENTER = 1

    if caption:
        cap_para = doc.add_paragraph(caption)
        try:
            cap_para.style = doc.styles["Caption"]
        except KeyError:
            cap_para.style = doc.styles["Normal"]
        cap_para.alignment = 1


def resize_image(
    src: str | Path,
    dest: str | Path,
    max_width_px: int = 1800,
    max_height_px: int = 2400,
) -> Path:
    """Resize an image to fit within max dimensions, preserving aspect ratio."""
    src, dest = Path(src), Path(dest)
    with PILImage.open(src) as img:
        img.thumbnail((max_width_px, max_height_px), PILImage.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest)
    return dest
