#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from utils.final_approval_report import save_final_approval_report
from utils.proposal_comparison import ProposalComparison
from utils.proposal_readiness import PhaseCoverage, ProposalReadiness


def _readiness() -> ProposalReadiness:
    return ProposalReadiness(
        selected_codes=["001-SUR-BASE"],
        resolved_codes=["001-SUR-BASE"],
        dependency_codes=[],
        validation_errors=[],
        validation_warnings=[],
        phase_coverage=[
            PhaseCoverage("001", "الأعمال التحضيرية", 1, 2),
            PhaseCoverage("002", "الحفر والمخلفات", 0, 0),
        ],
        missing_phase_names=["الحفر والمخلفات"],
        missing_content_codes=[],
        unapproved_content_codes=[],
        word_error_count=0,
        word_warning_count=0,
        total_pages=2,
        decision="caution",
        decision_ar="جاهز مع تحفظ",
        decision_reason_ar="توجد مراحل غير ممثلة.",
        cautions=["مراحل غير ممثلة: الحفر والمخلفات."],
    )


def test_save_final_approval_report_writes_html_and_json(tmp_path: Path) -> None:
    output_dir = tmp_path / "output" / "generated_documents"
    output_dir.mkdir(parents=True)

    html_path, json_path = save_final_approval_report(
        output_dir=output_dir,
        project_id="wastewater",
        owner_id="nwc",
        project_label="صرف صحي",
        owner_label="الشركة الوطنية للمياه",
        readiness=_readiness(),
        comparison=ProposalComparison(
            has_previous=True,
            previous_entry={"version_label": "PV-000001", "timestamp_display": "2026-04-30"},
            added_codes=["001-SUR-BASE"],
            removed_codes=["002-OLD-CODE"],
            current_page_count=2,
            previous_page_count=4,
        ),
        content_audits=[],
        template_vars={"engineer_name": "يوسف"},
    )

    assert html_path.exists()
    assert json_path.exists()
    html = html_path.read_text(encoding="utf-8")
    data = json_path.read_text(encoding="utf-8")
    assert "تقرير الاعتماد النهائي" in html
    assert "PV-000001" in html
    assert "جاهز مع تحفظ" in data
