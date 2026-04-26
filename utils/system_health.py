#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""System health checks for ATPAS data and content library.

The report is intentionally read-only. It helps users and AI agents understand
whether the app data is ready for building proposals before they touch JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from utils.registry_validator import validate_registry


@dataclass(frozen=True)
class HealthIssue:
    """One actionable health finding."""

    severity: str
    scope: str
    message_ar: str
    suggestion_ar: str = ""


@dataclass(frozen=True)
class SystemHealthReport:
    """Aggregated, UI-friendly health summary."""

    total_codes: int
    active_codes: int
    inactive_codes: int
    projects_count: int
    owners_count: int
    presets_count: int
    source_documents_count: int
    linked_documents_count: int
    missing_documents_count: int
    issues: list[HealthIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[HealthIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[HealthIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def info(self) -> list[HealthIssue]:
        return [i for i in self.issues if i.severity == "info"]

    @property
    def score(self) -> int:
        """Simple confidence score, designed to be understandable not magical."""
        penalty = len(self.errors) * 14 + len(self.warnings) * 4
        if self.missing_documents_count:
            penalty += min(18, self.missing_documents_count)
        return max(0, min(100, 100 - penalty))

    @property
    def status_ar(self) -> str:
        if self.errors:
            return "يحتاج إصلاح قبل البناء"
        if self.warnings:
            return "صالح مع تحذيرات"
        return "سليم وجاهز"


def build_system_health_report(
    registry_data: dict[str, Any],
    config_data: dict[str, Any],
    presets_data: dict[str, Any] | None = None,
    source_documents_dir: str | Path = "templates/source_documents",
) -> SystemHealthReport:
    """Build a read-only health report from loaded ATPAS data."""

    presets_data = presets_data or {"presets": {}}
    codes = _as_dict(registry_data.get("codes"))
    projects = _as_dict(config_data.get("projects"))
    owners = _as_dict(config_data.get("owner_specifications"))
    presets = _as_dict(presets_data.get("presets"))
    docs_dir = Path(source_documents_dir)
    doc_files = _list_docx_files(docs_dir)

    issues: list[HealthIssue] = []
    issues.extend(_registry_schema_issues(registry_data))
    issues.extend(_code_reference_issues(codes, projects, owners))
    issues.extend(_preset_reference_issues(presets, codes, projects, owners))

    linked_documents, missing_documents, content_issues = _content_issues(codes, docs_dir, doc_files)
    issues.extend(content_issues)

    active_codes = sum(1 for entry in codes.values() if entry.get("status") == "active")
    inactive_codes = sum(1 for entry in codes.values() if entry.get("status") != "active")

    if not projects:
        issues.append(HealthIssue(
            "error",
            "master_config.json",
            "لا توجد مشاريع معرفة داخل ملف الإعدادات.",
            "أضف المشاريع داخل master_config.json -> projects.",
        ))
    if not owners:
        issues.append(HealthIssue(
            "error",
            "master_config.json",
            "لا توجد جهات مالكة معرفة داخل ملف الإعدادات.",
            "أضف الجهات داخل master_config.json -> owner_specifications.",
        ))
    if not codes:
        issues.append(HealthIssue(
            "error",
            "codes_registry.json",
            "لا توجد أكواد داخل سجل الأكواد.",
            "راجع ملف codes_registry.json وتأكد من وجود الحقل codes.",
        ))

    return SystemHealthReport(
        total_codes=len(codes),
        active_codes=active_codes,
        inactive_codes=inactive_codes,
        projects_count=len(projects),
        owners_count=len(owners),
        presets_count=len(presets),
        source_documents_count=len(doc_files),
        linked_documents_count=linked_documents,
        missing_documents_count=missing_documents,
        issues=issues,
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_docx_files(docs_dir: Path) -> set[str]:
    if not docs_dir.exists() or not docs_dir.is_dir():
        return set()
    return {p.name for p in docs_dir.glob("*.docx") if p.is_file()}


def _registry_schema_issues(registry_data: Any) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    for scope, field, message in validate_registry(registry_data):
        issues.append(HealthIssue(
            "error",
            f"{scope}.{field}",
            f"مشكلة في بنية سجل الأكواد: {message}",
            "صحح الحقل المذكور أو انسخ كودًا صحيحًا مشابهًا وعدّل عليه.",
        ))
    return issues


def _code_reference_issues(
    codes: dict[str, Any],
    projects: dict[str, Any],
    owners: dict[str, Any],
) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    code_ids = set(codes)
    project_ids = set(projects)
    owner_ids = set(owners)

    for code_id, entry in codes.items():
        if not isinstance(entry, dict):
            continue

        unknown_projects = sorted(set(_iter_strings(entry.get("project_ids"))) - project_ids)
        if unknown_projects:
            issues.append(HealthIssue(
                "error",
                code_id,
                f"الكود مرتبط بمشاريع غير معرفة: {', '.join(unknown_projects)}.",
                "أضف المشروع في master_config.json أو صحح project_ids داخل الكود.",
            ))

        unknown_owners = sorted(set(_iter_strings(entry.get("applicable_owners"))) - owner_ids)
        if unknown_owners:
            issues.append(HealthIssue(
                "error",
                code_id,
                f"الكود مرتبط بجهات مالكة غير معرفة: {', '.join(unknown_owners)}.",
                "أضف الجهة في owner_specifications أو صحح applicable_owners.",
            ))

        missing_deps = sorted(set(_iter_strings(entry.get("dependencies"))) - code_ids)
        if missing_deps:
            issues.append(HealthIssue(
                "error",
                code_id,
                f"الكود يعتمد على أكواد غير موجودة: {', '.join(missing_deps)}.",
                "أضف الأكواد الناقصة أو احذفها من dependencies.",
            ))

    return issues


def _preset_reference_issues(
    presets: dict[str, Any],
    codes: dict[str, Any],
    projects: dict[str, Any],
    owners: dict[str, Any],
) -> list[HealthIssue]:
    issues: list[HealthIssue] = []
    code_ids = set(codes)
    project_ids = set(projects)
    owner_ids = set(owners)

    for preset_id, preset in presets.items():
        if not isinstance(preset, dict):
            issues.append(HealthIssue(
                "warning",
                str(preset_id),
                "نمط جاهز غير مقروء لأنه ليس كائن JSON صحيحًا.",
                "احذف النمط أو أعد إنشاءه من داخل التطبيق.",
            ))
            continue

        missing_codes = sorted(set(_iter_strings(preset.get("codes"))) - code_ids)
        if missing_codes:
            issues.append(HealthIssue(
                "warning",
                str(preset_id),
                f"النمط الجاهز يحتوي أكواد غير موجودة: {', '.join(missing_codes[:8])}.",
                "حدّث قائمة الأكواد داخل presets.json أو احفظ النمط من جديد.",
            ))

        unknown_projects = sorted(set(_iter_strings(preset.get("project_ids"))) - project_ids)
        if unknown_projects:
            issues.append(HealthIssue(
                "warning",
                str(preset_id),
                f"النمط الجاهز مرتبط بمشاريع غير معرفة: {', '.join(unknown_projects)}.",
                "صحح project_ids داخل هذا النمط.",
            ))

        owner_id = preset.get("owner_id")
        if isinstance(owner_id, str) and owner_id and owner_id not in owner_ids:
            issues.append(HealthIssue(
                "warning",
                str(preset_id),
                f"النمط الجاهز مرتبط بجهة مالكة غير معرفة: {owner_id}.",
                "صحح owner_id داخل هذا النمط.",
            ))

    return issues


def _content_issues(
    codes: dict[str, Any],
    docs_dir: Path,
    doc_files: set[str],
) -> tuple[int, int, list[HealthIssue]]:
    issues: list[HealthIssue] = []
    linked_documents = 0
    missing_codes: list[str] = []

    for code_id, entry in codes.items():
        if not isinstance(entry, dict) or entry.get("status") != "active":
            continue

        declared = entry.get("source_document")
        expected_name = declared if isinstance(declared, str) and declared.strip() else f"{code_id}.docx"
        if expected_name in doc_files:
            linked_documents += 1
        else:
            missing_codes.append(code_id)

    if not docs_dir.exists():
        issues.append(HealthIssue(
            "warning",
            "templates/source_documents",
            "مجلد ملفات Word غير موجود، وسيستخدم النظام نصوصًا عامة بدل المحتوى الحقيقي.",
            "أنشئ المجلد templates/source_documents وأضف ملفات Word باسم كل كود.",
        ))
    elif missing_codes:
        sample = ", ".join(missing_codes[:10])
        more = "" if len(missing_codes) <= 10 else f" ... و{len(missing_codes) - 10} كود آخر"
        issues.append(HealthIssue(
            "warning",
            "templates/source_documents",
            f"{len(missing_codes)} كود نشط لا يملك ملف Word مطابقًا. أمثلة: {sample}{more}.",
            "أضف ملفات DOCX للأكواد المهمة أو اربطها من مكتبة المحتوى.",
        ))

    return linked_documents, len(missing_codes), issues


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item
