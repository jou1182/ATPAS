#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Persist final pre-build approval decisions as HTML + JSON."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.json_manager import save_json
from utils.proposal_comparison import ProposalComparison
from utils.proposal_readiness import ProposalReadiness
from utils.word_content_audit import WordContentAudit, flatten_issues


def save_final_approval_report(
    *,
    output_dir: str | Path,
    project_id: str,
    owner_id: str,
    project_label: str,
    owner_label: str,
    readiness: ProposalReadiness,
    comparison: ProposalComparison,
    content_audits: list[WordContentAudit],
    template_vars: dict[str, str] | None = None,
) -> tuple[Path, Path]:
    """Save approval report and return (html_path, json_path)."""

    reports_dir = Path(output_dir).parent / "reports" / "final_approvals"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"approval_{project_id}_{owner_id}_{stamp}"
    html_path = reports_dir / f"{stem}.html"
    json_path = reports_dir / f"{stem}.json"

    payload = _approval_payload(
        project_id=project_id,
        owner_id=owner_id,
        project_label=project_label,
        owner_label=owner_label,
        readiness=readiness,
        comparison=comparison,
        content_audits=content_audits,
        template_vars=template_vars or {},
    )
    save_json(payload, json_path)
    html_path.write_text(render_final_approval_html(payload), encoding="utf-8")
    return html_path, json_path


def render_final_approval_html(payload: dict[str, Any]) -> str:
    """Render a standalone Arabic HTML report."""

    readiness = payload["readiness"]
    comparison = payload["comparison"]
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['phase'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{row['code_count']}</td>"
        f"<td>{row['page_count']}</td>"
        "</tr>"
        for row in readiness["phase_coverage"]
    )
    issue_rows = _issue_rows(payload.get("content_issues", []))
    comparison_html = _comparison_html(comparison)

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>تقرير اعتماد عرض ATPAS</title>
  <style>
    body {{
      font-family: Tajawal, sans-serif;
      direction: rtl;
      color: #121B28;
      background: #FEFCF7;
      margin: 30px;
      line-height: 1.65;
    }}
    h1 {{ color: #152433; border-bottom: 3px solid #C9921B; padding-bottom: 10px; }}
    h2 {{ color: #1F3A56; margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: #FFFFFF; margin: 10px 0 18px; }}
    th {{ background: #152433; color: #F5D48B; padding: 9px; }}
    td {{ border-bottom: 1px solid #ECE3D2; padding: 8px; vertical-align: top; }}
    .decision {{
      background: #FAF0DC;
      border-right: 5px solid #C9921B;
      border-radius: 8px;
      padding: 12px 14px;
      font-weight: 800;
    }}
    .ltr {{ direction: ltr; unicode-bidi: embed; font-family: Tajawal, sans-serif; }}
  </style>
</head>
<body>
  <h1>تقرير الاعتماد النهائي قبل البناء</h1>
  <div class="decision">
    القرار: {html.escape(readiness['decision_ar'])} - {html.escape(readiness['decision_reason_ar'])}
  </div>

  <h2>بيانات الاعتماد</h2>
  <table>
    <tr><th>البند</th><th>القيمة</th></tr>
    <tr><td>وقت الاعتماد</td><td>{html.escape(payload['approved_at'])}</td></tr>
    <tr><td>المشروع</td><td>{html.escape(payload['project_label'])}</td></tr>
    <tr><td>الجهة المالكة</td><td>{html.escape(payload['owner_label'])}</td></tr>
    <tr><td>الأكواد النهائية</td><td>{len(readiness['resolved_codes'])}</td></tr>
    <tr><td>الصفحات التقديرية</td><td>{readiness['total_pages']}</td></tr>
  </table>

  {comparison_html}

  <h2>تغطية مراحل المشروع</h2>
  <table>
    <tr><th>المرحلة</th><th>الحالة</th><th>الأكواد</th><th>الصفحات</th></tr>
    {rows}
  </table>

  <h2>ملاحظات الاعتماد</h2>
  <table>
    <tr><th>النوع</th><th>النص</th></tr>
    {_list_rows('موانع', readiness.get('blockers', []))}
    {_list_rows('تحفظ', readiness.get('cautions', []))}
  </table>

  <h2>ملاحظات محتوى Word</h2>
  <table>
    <tr><th>النوع</th><th>الكود</th><th>الملاحظة</th></tr>
    {issue_rows}
  </table>
</body>
</html>"""


def _approval_payload(
    *,
    project_id: str,
    owner_id: str,
    project_label: str,
    owner_label: str,
    readiness: ProposalReadiness,
    comparison: ProposalComparison,
    content_audits: list[WordContentAudit],
    template_vars: dict[str, str],
) -> dict[str, Any]:
    content_issues = flatten_issues(content_audits)
    return {
        "approved_at": datetime.now().isoformat(timespec="seconds"),
        "project_id": project_id,
        "owner_id": owner_id,
        "project_label": project_label,
        "owner_label": owner_label,
        "template_vars": template_vars,
        "readiness": {
            "decision": readiness.decision,
            "decision_ar": readiness.decision_ar,
            "decision_reason_ar": readiness.decision_reason_ar,
            "selected_codes": readiness.selected_codes,
            "resolved_codes": readiness.resolved_codes,
            "dependency_codes": readiness.dependency_codes,
            "total_pages": readiness.total_pages,
            "missing_content_codes": readiness.missing_content_codes,
            "unapproved_content_codes": readiness.unapproved_content_codes,
            "word_error_count": readiness.word_error_count,
            "word_warning_count": readiness.word_warning_count,
            "blockers": readiness.blockers,
            "cautions": readiness.cautions,
            "phase_coverage": [
                {
                    "category": phase.category,
                    "phase": phase.name_ar,
                    "status": "مغطاة" if phase.covered else "غير ممثلة",
                    "code_count": phase.code_count,
                    "page_count": phase.page_count,
                }
                for phase in readiness.phase_coverage
            ],
        },
        "comparison": {
            "has_previous": comparison.has_previous,
            "previous_label": comparison.previous_label,
            "previous_timestamp": comparison.previous_timestamp,
            "added_codes": comparison.added_codes,
            "removed_codes": comparison.removed_codes,
            "shared_codes": comparison.shared_codes,
            "previous_page_count": comparison.previous_page_count,
            "current_page_count": comparison.current_page_count,
            "page_delta": comparison.page_delta,
        },
        "content_issues": [
            {
                "severity": issue.severity,
                "code_id": issue.code_id,
                "message_ar": issue.message_ar,
                "suggestion_ar": issue.suggestion_ar,
            }
            for issue in content_issues
        ],
    }


def _comparison_html(comparison: dict[str, Any]) -> str:
    if not comparison.get("has_previous"):
        return "<h2>المقارنة مع آخر عرض مشابه</h2><p>لا يوجد عرض سابق مشابه في سجل الإصدارات.</p>"
    return f"""
  <h2>المقارنة مع آخر عرض مشابه</h2>
  <table>
    <tr><th>البند</th><th>القيمة</th></tr>
    <tr><td>العرض السابق</td><td>{html.escape(comparison.get('previous_label', ''))}</td></tr>
    <tr><td>تاريخ العرض السابق</td><td>{html.escape(comparison.get('previous_timestamp', ''))}</td></tr>
    <tr><td>أكواد مضافة</td><td>{', '.join(comparison.get('added_codes', [])) or 'لا يوجد'}</td></tr>
    <tr><td>أكواد محذوفة</td><td>{', '.join(comparison.get('removed_codes', [])) or 'لا يوجد'}</td></tr>
    <tr><td>فرق الصفحات</td><td>{comparison.get('page_delta', 0)}</td></tr>
  </table>
"""


def _issue_rows(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "<tr><td colspan='3'>لا توجد ملاحظات محتوى.</td></tr>"
    return "".join(
        "<tr>"
        f"<td>{html.escape(str(issue.get('severity', '')))}</td>"
        f"<td class='ltr'>{html.escape(str(issue.get('code_id', '')))}</td>"
        f"<td>{html.escape(str(issue.get('message_ar', '')))}</td>"
        "</tr>"
        for issue in issues
    )


def _list_rows(label: str, items: list[str]) -> str:
    if not items:
        return ""
    return "".join(
        f"<tr><td>{html.escape(label)}</td><td>{html.escape(item)}</td></tr>"
        for item in items
    )
