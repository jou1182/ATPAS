#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils.proposal_readiness import analyze_proposal_readiness
from utils.word_content_audit import WordContentAudit, WordContentIssue


def _codes() -> dict[str, dict]:
    return {
        "001-SUR-BASE": {
            "category": "001",
            "sequence_order": 1,
            "page_count": 2,
            "dependencies": [],
        },
        "002-EXC-FINE": {
            "category": "002",
            "sequence_order": 2,
            "page_count": 3,
            "dependencies": ["001-SUR-BASE"],
        },
        "003-PIP-SEW": {
            "category": "003",
            "sequence_order": 3,
            "page_count": 4,
            "dependencies": ["002-EXC-FINE"],
        },
        "004-TST-LEK": {
            "category": "004",
            "sequence_order": 4,
            "page_count": 2,
            "dependencies": ["003-PIP-SEW"],
        },
        "005-HND-FIN": {
            "category": "005",
            "sequence_order": 5,
            "page_count": 1,
            "dependencies": ["004-TST-LEK"],
        },
    }


def _ok_audits(code_ids: list[str]) -> list[WordContentAudit]:
    return [
        WordContentAudit(code_id=code_id, path=f"{code_id}.docx", exists=True)
        for code_id in code_ids
    ]


def test_readiness_ready_when_all_phases_and_content_clean() -> None:
    selected = list(_codes())

    result = analyze_proposal_readiness(
        codes=_codes(),
        selected_codes=selected,
        content_audits=_ok_audits(selected),
    )

    assert result.decision == "ready"
    assert result.can_build is True
    assert result.missing_phase_names == []
    assert result.dependency_codes == []
    assert result.total_pages == 12


def test_readiness_caution_for_auto_dependencies_and_missing_phases() -> None:
    result = analyze_proposal_readiness(
        codes=_codes(),
        selected_codes=["003-PIP-SEW"],
        content_audits=_ok_audits(["003-PIP-SEW"]),
    )

    assert result.decision == "caution"
    assert result.can_build is True
    assert result.dependency_codes == ["001-SUR-BASE", "002-EXC-FINE"]
    assert "الاختبارات والفحوصات" in result.missing_phase_names
    assert "الإنهاء والتسليم" in result.missing_phase_names


def test_readiness_caution_for_missing_word_content() -> None:
    result = analyze_proposal_readiness(
        codes=_codes(),
        selected_codes=["001-SUR-BASE"],
        content_audits=[
            WordContentAudit(
                code_id="001-SUR-BASE",
                path="",
                exists=False,
                issues=[
                    WordContentIssue(
                        "warning",
                        "001-SUR-BASE",
                        "لا يوجد ملف Word مطابق لهذا الكود.",
                    )
                ],
            )
        ],
    )

    assert result.decision == "caution"
    assert result.missing_content_codes == ["001-SUR-BASE"]
    assert result.word_warning_count == 1


def test_readiness_blocked_for_validation_or_word_errors() -> None:
    result = analyze_proposal_readiness(
        codes=_codes(),
        selected_codes=["001-SUR-BASE"],
        validation_errors=["الكود غير مخصص للجهة"],
        content_audits=[
            WordContentAudit(
                code_id="001-SUR-BASE",
                path="001-SUR-BASE.docx",
                exists=True,
                issues=[
                    WordContentIssue(
                        "error",
                        "001-SUR-BASE",
                        "ملف Word فارغ.",
                    )
                ],
            )
        ],
    )

    assert result.decision == "blocked"
    assert result.can_build is False
    assert result.word_error_count == 1
    assert result.blockers


def test_readiness_caution_for_unapproved_content() -> None:
    result = analyze_proposal_readiness(
        codes=_codes(),
        selected_codes=["001-SUR-BASE"],
        content_audits=_ok_audits(["001-SUR-BASE"]),
        unapproved_content_codes=["001-SUR-BASE"],
    )

    assert result.decision == "caution"
    assert result.unapproved_content_codes == ["001-SUR-BASE"]
    assert any("غير معتمد" in item for item in result.cautions)
