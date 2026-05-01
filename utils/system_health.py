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
from utils.word_content_audit import audit_docx_file


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
    checked_word_documents_count: int = 0
    word_content_issue_count: int = 0
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
        if self.word_content_issue_count:
            penalty += min(12, self.word_content_issue_count * 2)
        return max(0, min(100, 100 - penalty))

    @property
    def status_ar(self) -> str:
        if self.errors:
            return "يحتاج إصلاح قبل البناء"
        if self.warnings:
            return "صالح مع تحذيرات"
        return "سليم وجاهز"


def render_markdown_report(report: SystemHealthReport) -> str:
    """Render the health report as a shareable Arabic Markdown document."""
    lines = [
        "# تقرير صحة نظام ATPAS",
        "",
        "## الملخص التنفيذي",
        "",
        f"- درجة الجاهزية: **{report.score}%**",
        f"- الحالة: **{report.status_ar}**",
        f"- الأخطاء: **{len(report.errors)}**",
        f"- التحذيرات: **{len(report.warnings)}**",
        "",
        "## المؤشرات",
        "",
        "| المؤشر | القيمة |",
        "|---|---:|",
        f"| الأكواد الكلية | {report.total_codes} |",
        f"| الأكواد النشطة | {report.active_codes} |",
        f"| الأكواد غير النشطة | {report.inactive_codes} |",
        f"| المشاريع | {report.projects_count} |",
        f"| الجهات المالكة | {report.owners_count} |",
        f"| الأنماط الجاهزة | {report.presets_count} |",
        f"| ملفات Word الموجودة | {report.source_documents_count} |",
        f"| الأكواد المرتبطة بمحتوى Word | {report.linked_documents_count} |",
        f"| أكواد بلا ملف Word مطابق | {report.missing_documents_count} |",
        f"| ملفات Word المفحوصة | {report.checked_word_documents_count} |",
        f"| ملاحظات جودة محتوى Word | {report.word_content_issue_count} |",
        "",
        "## الملاحظات والإجراءات المقترحة",
        "",
    ]

    if not report.issues:
        lines.append("- لا توجد أخطاء أو تحذيرات. النظام جاهز للبناء.")
    else:
        lines.extend([
            "| النوع | المكان | الملاحظة | الإجراء المقترح |",
            "|---|---|---|---|",
        ])
        for issue in report.issues:
            lines.append(
                "| "
                f"{_severity_text(issue.severity)} | "
                f"{_md_escape(issue.scope)} | "
                f"{_md_escape(issue.message_ar)} | "
                f"{_md_escape(issue.suggestion_ar or 'راجع الملف المشار إليه.')} |"
            )

    lines.extend([
        "",
        "## قرار الجودة",
        "",
        _quality_decision(report),
        "",
    ])
    return "\n".join(lines)


def save_system_health_report(report: SystemHealthReport, path: str | Path) -> Path:
    """Write a Markdown health report using a Windows-friendly UTF-8 BOM."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown_report(report), encoding="utf-8-sig")
    return target


def render_html_report(report: SystemHealthReport) -> str:
    """Render the health report as a standalone Arabic HTML document."""
    issue_rows = ""
    if report.issues:
        issue_rows = "\n".join(
            "<tr>"
            f"<td>{_severity_text(issue.severity)}</td>"
            f"<td>{_html_escape(issue.scope)}</td>"
            f"<td>{_html_escape(issue.message_ar)}</td>"
            f"<td>{_html_escape(issue.suggestion_ar or 'راجع الملف المشار إليه.')}</td>"
            "</tr>"
            for issue in report.issues
        )
    else:
        issue_rows = (
            "<tr><td colspan='4' class='ok'>لا توجد أخطاء أو تحذيرات. "
            "النظام جاهز للبناء.</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>تقرير صحة نظام ATPAS</title>
  <style>
    body {{
      font-family: Tajawal, sans-serif;
      direction: rtl;
      color: #121B28;
      background: #FEFCF7;
      margin: 32px;
      line-height: 1.65;
    }}
    h1 {{ color: #152433; border-bottom: 3px solid #C9921B; padding-bottom: 10px; }}
    h2 {{ color: #1F3A56; margin-top: 28px; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 12px;
      margin: 18px 0;
    }}
    .card {{
      background: #FAF0DC;
      border: 1px solid #D5CFBF;
      border-radius: 12px;
      padding: 14px;
      text-align: center;
    }}
    .value {{ font-size: 22px; font-weight: 900; color: #152433; }}
    table {{ width: 100%; border-collapse: collapse; background: #FFFFFF; }}
    th {{ background: #152433; color: #F5D48B; padding: 9px; }}
    td {{ border-bottom: 1px solid #ECE3D2; padding: 9px; vertical-align: top; }}
    .ok {{ color: #2B7549; font-weight: 800; }}
    .decision {{
      background: #EEF3FA;
      border-right: 5px solid #1F4F7D;
      padding: 12px 14px;
      border-radius: 8px;
    }}
  </style>
</head>
<body>
  <h1>تقرير صحة نظام ATPAS</h1>
  <div class="summary">
    <div class="card"><div>درجة الجاهزية</div><div class="value">{report.score}%</div></div>
    <div class="card"><div>الحالة</div><div class="value">{_html_escape(report.status_ar)}</div></div>
    <div class="card"><div>الأخطاء</div><div class="value">{len(report.errors)}</div></div>
    <div class="card"><div>التحذيرات</div><div class="value">{len(report.warnings)}</div></div>
  </div>
  <h2>المؤشرات</h2>
  <table>
    <tr><th>المؤشر</th><th>القيمة</th></tr>
    <tr><td>الأكواد الكلية</td><td>{report.total_codes}</td></tr>
    <tr><td>الأكواد النشطة</td><td>{report.active_codes}</td></tr>
    <tr><td>الأكواد غير النشطة</td><td>{report.inactive_codes}</td></tr>
    <tr><td>المشاريع</td><td>{report.projects_count}</td></tr>
    <tr><td>الجهات المالكة</td><td>{report.owners_count}</td></tr>
    <tr><td>الأنماط الجاهزة</td><td>{report.presets_count}</td></tr>
    <tr><td>ملفات Word الموجودة</td><td>{report.source_documents_count}</td></tr>
    <tr><td>الأكواد المرتبطة بمحتوى Word</td><td>{report.linked_documents_count}</td></tr>
    <tr><td>أكواد بلا ملف Word مطابق</td><td>{report.missing_documents_count}</td></tr>
    <tr><td>ملفات Word المفحوصة</td><td>{report.checked_word_documents_count}</td></tr>
    <tr><td>ملاحظات جودة محتوى Word</td><td>{report.word_content_issue_count}</td></tr>
  </table>
  <h2>الملاحظات والإجراءات المقترحة</h2>
  <table>
    <tr><th>النوع</th><th>المكان</th><th>الملاحظة</th><th>الإجراء المقترح</th></tr>
    {issue_rows}
  </table>
  <h2>قرار الجودة</h2>
  <div class="decision">{_html_escape(_quality_decision(report))}</div>
</body>
</html>"""


def save_html_report(report: SystemHealthReport, path: str | Path) -> Path:
    """Write a standalone HTML health report."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_html_report(report), encoding="utf-8")
    return target


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

    (
        linked_documents,
        missing_documents,
        checked_word_documents,
        word_content_issue_count,
        content_issues,
    ) = _content_issues(codes, docs_dir, doc_files)
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
        checked_word_documents_count=checked_word_documents,
        word_content_issue_count=word_content_issue_count,
        issues=issues,
    )


def _quality_decision(report: SystemHealthReport) -> str:
    if report.errors:
        return "لا يوصى ببناء أو تسليم عرض فني قبل إصلاح الأخطاء المذكورة."
    if report.warnings:
        return (
            "يمكن استخدام النظام داخليًا، لكن لا يوصى بالتسليم التجاري النهائي "
            "قبل مراجعة التحذيرات، خصوصًا ملفات Word الناقصة."
        )
    return "النظام جاهز للبناء والتسليم من منظور البيانات والمحتوى المتاح."


def _severity_text(severity: str) -> str:
    labels = {
        "error": "خطأ",
        "warning": "تحذير",
        "info": "معلومة",
    }
    return labels.get(severity, severity)


def _md_escape(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ")
    return text.replace("|", "\\|").strip()


def _html_escape(value: Any) -> str:
    import html

    return html.escape(str(value), quote=True)


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
) -> tuple[int, int, int, int, list[HealthIssue]]:
    issues: list[HealthIssue] = []
    linked_documents = 0
    checked_word_documents = 0
    word_content_issue_count = 0
    missing_codes: list[str] = []

    for code_id, entry in codes.items():
        if not isinstance(entry, dict) or entry.get("status") != "active":
            continue

        declared = entry.get("source_document")
        expected_name = declared if isinstance(declared, str) and declared.strip() else f"{code_id}.docx"
        if expected_name in doc_files:
            linked_documents += 1
            audit = audit_docx_file(docs_dir / expected_name, code_id=code_id, code_data=entry)
            checked_word_documents += 1
            for audit_issue in audit.issues:
                word_content_issue_count += 1
                issues.append(HealthIssue(
                    audit_issue.severity,
                    f"templates/source_documents/{expected_name}",
                    f"{code_id}: {audit_issue.message_ar}",
                    audit_issue.suggestion_ar,
                ))
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

    return (
        linked_documents,
        len(missing_codes),
        checked_word_documents,
        word_content_issue_count,
        issues,
    )


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item


if __name__ == "__main__":
    import sys

    from utils.json_manager import load_json

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    current_report = build_system_health_report(
        registry_data=load_json("codes_registry.json"),
        config_data=load_json("master_config.json"),
        presets_data=load_json("presets.json"),
        source_documents_dir=Path("templates/source_documents"),
    )
    print(render_markdown_report(current_report))
