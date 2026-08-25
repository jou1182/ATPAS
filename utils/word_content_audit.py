#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Lightweight quality audit for ATPAS source Word content files.

The goal is not to judge writing quality.  It catches delivery risks that are
easy to miss when source documents are collected from many engineers:

- unreadable / corrupt .docx files
- empty content files
- duplicated activity headings at the top of the source file
- externally linked media or hyperlinks
- floating shapes / text boxes that often shift when documents are merged
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from docx import Document
from docx.oxml.ns import qn

from utils.content_library import ContentLibrary

# Audit results are immutable dataclasses — safe to cache per file version.
# Key: (resolved path, mtime_ns, size, code_id, activity_name_ar).
# Parsing a docx costs ~50-80 ms; system health audits ~65 files per run,
# so caching turns repeat checks from seconds into milliseconds.
_AUDIT_CACHE: dict[tuple, WordContentAudit] = {}


def clear_audit_cache() -> None:
    """Drop cached audit results (e.g. after bulk content changes)."""
    _AUDIT_CACHE.clear()


@dataclass(frozen=True)
class WordContentIssue:
    """One content-library quality finding."""

    severity: str
    code_id: str
    message_ar: str
    suggestion_ar: str = ""


@dataclass(frozen=True)
class WordContentAudit:
    """Audit result for a single code's source document."""

    code_id: str
    path: str
    exists: bool
    paragraph_count: int = 0
    table_count: int = 0
    inline_image_count: int = 0
    external_link_count: int = 0
    floating_shape_count: int = 0
    has_rtl_marker: bool = False
    issues: list[WordContentIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[WordContentIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[WordContentIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return self.exists and not self.errors and not self.warnings


def audit_code_content(
    code_id: str,
    code_data: dict,
    content_library: ContentLibrary | None = None,
) -> WordContentAudit:
    """Audit the source .docx attached to one code.

    Missing files are reported as a warning, not an error, because ATPAS can
    still build a proposal using placeholder text.
    """

    lib = content_library or ContentLibrary()
    source_path = lib.find(code_id)
    if source_path is None:
        return WordContentAudit(
            code_id=code_id,
            path="",
            exists=False,
            issues=[
                WordContentIssue(
                    "warning",
                    code_id,
                    "لا يوجد ملف Word مطابق لهذا الكود.",
                    f"أضف ملفًا باسم {code_id}.docx داخل templates/source_documents.",
                )
            ],
        )

    return audit_docx_file(source_path, code_id=code_id, code_data=code_data)


def audit_docx_file(
    path: str | Path,
    *,
    code_id: str,
    code_data: dict | None = None,
) -> WordContentAudit:
    """Inspect a .docx file and return a structured Arabic audit."""

    code_data = code_data or {}
    source_path = Path(path)
    issues: list[WordContentIssue] = []

    if not source_path.exists():
        return WordContentAudit(
            code_id=code_id,
            path=str(source_path),
            exists=False,
            issues=[
                WordContentIssue(
                    "warning",
                    code_id,
                    "مسار ملف Word المسجل غير موجود.",
                    "صحح مسار الملف أو ضع نسخة صحيحة في مكتبة المحتوى.",
                )
            ],
        )

    try:
        _st = source_path.stat()
        cache_key: tuple | None = (
            str(source_path.resolve()),
            _st.st_mtime_ns,
            _st.st_size,
            code_id,
            str(code_data.get("activity_name_ar", "")),
        )
    except OSError:
        cache_key = None
    if cache_key is not None and cache_key in _AUDIT_CACHE:
        return _AUDIT_CACHE[cache_key]

    try:
        doc = Document(str(source_path))
    except Exception as exc:  # noqa: BLE001
        audit = WordContentAudit(
            code_id=code_id,
            path=str(source_path),
            exists=True,
            issues=[
                WordContentIssue(
                    "error",
                    code_id,
                    f"ملف Word غير قابل للقراءة: {exc}",
                    "افتح الملف في Microsoft Word واحفظ نسخة DOCX جديدة.",
                )
            ],
        )
        if cache_key is not None:
            _AUDIT_CACHE[cache_key] = audit
        return audit

    non_empty_paragraphs = [p for p in doc.paragraphs if p.text.strip()]
    paragraph_count = len(non_empty_paragraphs)
    table_count = len(doc.tables)
    inline_image_count = len(doc.inline_shapes)
    external_link_count = _count_external_relationships(doc)
    floating_shape_count = _count_floating_shapes(doc)
    has_rtl_marker = _has_any_rtl_marker(doc)

    if paragraph_count == 0 and table_count == 0 and inline_image_count == 0:
        issues.append(
            WordContentIssue(
                "error",
                code_id,
                "ملف Word فارغ ولا يحتوي نصًا أو جداول أو صورًا.",
                "أضف محتوى فنيًا حقيقيًا قبل اعتماد هذا الكود.",
            )
        )

    first_text = non_empty_paragraphs[0].text.strip() if non_empty_paragraphs else ""
    activity_name_ar = str(code_data.get("activity_name_ar", "")).strip()
    if first_text and _looks_like_duplicate_heading(first_text, code_id, activity_name_ar):
        issues.append(
            WordContentIssue(
                "warning",
                code_id,
                "يبدو أن أول سطر في الملف هو عنوان النشاط، والنظام يضيف العنوان تلقائيًا.",
                "احذف عنوان النشاط من بداية ملف المصدر لتجنب ظهوره مرتين في العرض.",
            )
        )

    if external_link_count:
        issues.append(
            WordContentIssue(
                "warning",
                code_id,
                f"الملف يحتوي {external_link_count} رابطًا خارجيًا أو وسيطًا مرتبطًا من خارج الملف.",
                "ضمّن الصور والملفات داخل Word بدل ربطها بمسارات خارجية.",
            )
        )

    if floating_shape_count:
        issues.append(
            WordContentIssue(
                "warning",
                code_id,
                f"الملف يحتوي {floating_shape_count} عنصرًا عائمًا أو مربع نص قد يتحرك بعد الدمج.",
                "استخدم صورًا Inline with Text وتجنب مربعات النص للعناصر الفنية المهمة.",
            )
        )

    if paragraph_count > 0 and not has_rtl_marker:
        issues.append(
            WordContentIssue(
                "warning",
                code_id,
                "لم يتم العثور على علامة اتجاه RTL داخل ملف المصدر.",
                "يفضل ضبط اتجاه فقرات الملف من اليمين إلى اليسار قبل اعتماده.",
            )
        )

    audit = WordContentAudit(
        code_id=code_id,
        path=str(source_path),
        exists=True,
        paragraph_count=paragraph_count,
        table_count=table_count,
        inline_image_count=inline_image_count,
        external_link_count=external_link_count,
        floating_shape_count=floating_shape_count,
        has_rtl_marker=has_rtl_marker,
        issues=issues,
    )
    if cache_key is not None:
        _AUDIT_CACHE[cache_key] = audit
    return audit


def audit_selected_content(
    codes: dict[str, dict],
    selected_codes: Iterable[str],
    content_library: ContentLibrary | None = None,
) -> list[WordContentAudit]:
    """Audit content files for a selected code list."""

    lib = content_library or ContentLibrary()
    audits: list[WordContentAudit] = []
    for code_id in selected_codes:
        code_data = codes.get(code_id, {})
        if code_data.get("is_custom") or code_data.get("_custom"):
            continue
        audits.append(audit_code_content(code_id, code_data, lib))
    return audits


def flatten_issues(audits: Iterable[WordContentAudit]) -> list[WordContentIssue]:
    """Return all issues from many audits in their original order."""

    issues: list[WordContentIssue] = []
    for audit in audits:
        issues.extend(audit.issues)
    return issues


def _looks_like_duplicate_heading(first_text: str, code_id: str, activity_name_ar: str) -> bool:
    normalized_first = _normalize_heading(first_text)
    if not _is_heading_sized_text(normalized_first):
        return False
    if code_id and code_id.lower() in normalized_first.lower():
        return True
    if activity_name_ar:
        name = _normalize_heading(activity_name_ar)
        if name and (name in normalized_first or normalized_first in name):
            return True
    return False


def _is_heading_sized_text(text: str) -> bool:
    """Avoid flagging normal opening paragraphs that mention the activity name."""

    words = text.split()
    return len(text) <= 120 and len(words) <= 14


def _normalize_heading(text: str) -> str:
    return " ".join(text.replace("—", " ").replace("-", " ").split())


def _count_external_relationships(doc: Document) -> int:
    count = 0
    try:
        for rel in doc.part.rels.values():
            if getattr(rel, "is_external", False):
                count += 1
    except Exception:  # noqa: BLE001
        return 0
    return count


def _count_floating_shapes(doc: Document) -> int:
    root = doc.element
    anchors = root.xpath(".//*[local-name()='anchor']")
    text_boxes = root.xpath(".//*[local-name()='txbxContent']")
    return len(anchors) + len(text_boxes)


def _has_any_rtl_marker(doc: Document) -> bool:
    bidi_tag = qn("w:bidi")
    try:
        if doc.settings.element.find(bidi_tag) is not None:
            return True
        for paragraph in doc.paragraphs:
            p_pr = paragraph._p.pPr
            if p_pr is not None and p_pr.find(bidi_tag) is not None:
                return True
        normal = doc.styles["Normal"]
        p_pr = normal.element.pPr
        return p_pr is not None and p_pr.find(bidi_tag) is not None
    except Exception:  # noqa: BLE001
        return False
