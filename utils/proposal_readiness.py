#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Final proposal readiness analysis before document generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from engine.dependency_resolver import DependencyResolver
from utils.word_content_audit import WordContentAudit, flatten_issues


PHASES: dict[str, str] = {
    "001": "الأعمال التحضيرية",
    "002": "الحفر والمخلفات",
    "003": "التركيب والتوصيل",
    "004": "الاختبارات والفحوصات",
    "005": "الإنهاء والتسليم",
}


@dataclass(frozen=True)
class PhaseCoverage:
    """Coverage summary for one technical phase."""

    category: str
    name_ar: str
    code_count: int = 0
    page_count: int = 0

    @property
    def covered(self) -> bool:
        return self.code_count > 0


@dataclass(frozen=True)
class ProposalReadiness:
    """One final decision object for the pre-build review."""

    selected_codes: list[str]
    resolved_codes: list[str]
    dependency_codes: list[str]
    validation_errors: list[str]
    validation_warnings: list[str]
    phase_coverage: list[PhaseCoverage]
    missing_phase_names: list[str]
    missing_content_codes: list[str]
    unapproved_content_codes: list[str]
    word_error_count: int
    word_warning_count: int
    total_pages: int
    decision: str
    decision_ar: str
    decision_reason_ar: str
    blockers: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)

    @property
    def can_build(self) -> bool:
        return self.decision != "blocked"


def analyze_proposal_readiness(
    *,
    codes: dict[str, dict],
    selected_codes: Iterable[str],
    validation_errors: Iterable[str] = (),
    validation_warnings: Iterable[str] = (),
    content_audits: Iterable[WordContentAudit] = (),
    unapproved_content_codes: Iterable[str] = (),
    resolver: DependencyResolver | None = None,
) -> ProposalReadiness:
    """Analyze the proposal as the user will actually build it."""

    selected = list(selected_codes)
    resolver = resolver or DependencyResolver(codes)
    resolved = resolver.resolve(selected) if selected else []
    selected_set = set(selected)
    dependency_codes = [cid for cid in resolved if cid not in selected_set]

    audits = list(content_audits)
    content_issues = flatten_issues(audits)
    missing_content = [audit.code_id for audit in audits if not audit.exists]
    unapproved = list(unapproved_content_codes)
    word_errors = [issue for issue in content_issues if issue.severity == "error"]
    word_warnings = [issue for issue in content_issues if issue.severity == "warning"]

    coverage = _phase_coverage(codes, resolved)
    missing_phases = [phase.name_ar for phase in coverage if not phase.covered]
    total_pages = sum(_safe_int(codes.get(cid, {}).get("page_count"), 0) for cid in resolved)

    errors = list(validation_errors)
    warnings = list(validation_warnings)
    blockers: list[str] = []
    cautions: list[str] = []

    if errors:
        blockers.append(f"{len(errors)} خطأ تحقق يمنع البناء.")
    if word_errors:
        blockers.append(f"{len(word_errors)} مشكلة حرجة في ملفات Word.")
    if dependency_codes:
        cautions.append(f"سيضيف النظام {len(dependency_codes)} كود تبعية تلقائيًا.")
    if warnings:
        cautions.append(f"{len(warnings)} تحذير تحقق يحتاج مراجعة.")
    if missing_phases:
        cautions.append(f"مراحل غير ممثلة: {', '.join(missing_phases)}.")
    if missing_content:
        cautions.append(f"{len(missing_content)} كود بلا محتوى Word حقيقي.")
    if unapproved:
        cautions.append(f"{len(unapproved)} ملف Word موجود لكنه غير معتمد بعد.")
    quality_warnings = [
        issue for issue in word_warnings
        if issue.code_id not in set(missing_content)
    ]
    if quality_warnings:
        cautions.append(f"{len(quality_warnings)} ملاحظة جودة على ملفات Word.")

    if blockers:
        decision = "blocked"
        decision_ar = "غير جاهز"
        reason = "توجد مشاكل تمنع البناء الآمن."
    elif cautions:
        decision = "caution"
        decision_ar = "جاهز مع تحفظ"
        reason = "يمكن البناء، لكن يلزم اعتماد الملاحظات قبل التسليم."
    else:
        decision = "ready"
        decision_ar = "جاهز للتسليم"
        reason = "التغطية والمحتوى والتحقق بحالة سليمة."

    return ProposalReadiness(
        selected_codes=selected,
        resolved_codes=resolved,
        dependency_codes=dependency_codes,
        validation_errors=errors,
        validation_warnings=warnings,
        phase_coverage=coverage,
        missing_phase_names=missing_phases,
        missing_content_codes=missing_content,
        unapproved_content_codes=unapproved,
        word_error_count=len(word_errors),
        word_warning_count=len(word_warnings),
        total_pages=total_pages,
        decision=decision,
        decision_ar=decision_ar,
        decision_reason_ar=reason,
        blockers=blockers,
        cautions=cautions,
    )


def _phase_coverage(codes: dict[str, dict], resolved_codes: list[str]) -> list[PhaseCoverage]:
    buckets: dict[str, dict[str, int]] = {
        category: {"code_count": 0, "page_count": 0}
        for category in PHASES
    }
    for code_id in resolved_codes:
        code = codes.get(code_id, {})
        category = str(code.get("category", "")).strip()
        if category not in buckets:
            continue
        buckets[category]["code_count"] += 1
        buckets[category]["page_count"] += _safe_int(code.get("page_count"), 0)

    return [
        PhaseCoverage(
            category=category,
            name_ar=name_ar,
            code_count=buckets[category]["code_count"],
            page_count=buckets[category]["page_count"],
        )
        for category, name_ar in PHASES.items()
    ]


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
