#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path
from typing import Dict, List, Tuple

from engine.rules import is_alternative_dependency_set as _rules_alt_deps
from engine.types import CodeRegistry
from utils.json_manager import load_json

# Owner spec files location
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OWNER_SPECS_DIR = _PROJECT_ROOT / "metadata" / "owner_specifications"

# نمط معرّف الكود الصالح: NNN-AAA-BBB  (حتى 8 محارف لكل مقطع)
_CODE_ID_PATTERN = re.compile(r"^\d{3}-[A-Z]{2,8}-[A-Z]{2,8}$")


class Validator:
    """
    Validates a list of selected codes against owner and project rules.

    Usage:
        validator = Validator(registry_codes, owner_specs_dir)
        is_valid, errors, warnings = validator.validate(codes, "nwc", "wastewater")
    """

    def __init__(
        self,
        codes: CodeRegistry,
        owner_specs_dir: str | Path = _OWNER_SPECS_DIR,
    ) -> None:
        if not isinstance(codes, dict):
            raise TypeError(
                f"codes must be a dict[str, dict], got {type(codes).__name__}"
            )
        self._codes: CodeRegistry = codes
        self._owner_specs_dir = Path(owner_specs_dir)
        self._owner_cache: Dict[str, Dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        selected_codes: List[str],
        owner_id: str,
        project_id: str | List[str],
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate selected_codes for the given owner and project.

        Returns:
            (is_valid, errors, warnings)
            errors   — blocking issues that must be resolved
            warnings — non-blocking suggestions
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Accept str or list for backward compatibility
        project_ids: List[str] = (
            [project_id] if isinstance(project_id, str) else list(project_id)
        )

        owner_spec = self._load_owner(owner_id)

        for code_id in selected_codes:
            self._check_format(code_id, errors)
            self._check_exists(code_id, errors)
            if code_id not in self._codes:
                continue
            self._check_active(code_id, errors)
            self._check_project_multi(code_id, project_ids, errors)
            self._check_owner(code_id, owner_id, errors)

        self._check_forbidden(selected_codes, owner_spec, errors)
        self._check_mandatory(selected_codes, owner_spec, warnings)
        self._check_dependencies(selected_codes, project_ids, warnings)
        self._check_excavation_context(selected_codes, project_ids, errors, warnings)

        return len(errors) == 0, errors, warnings

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_format(self, code_id: str, errors: List[str]) -> None:
        """Reject malformed or potentially unsafe code IDs before any filesystem use.

        Custom codes (is_custom: True) use the 999-CUS-NNN format which differs
        from the standard NNN-AAA-BBB pattern — they are exempt from the regex check.
        """
        if any(ch in code_id for ch in ("/", "\\", "..", "~", "\x00")):
            errors.append(f"الكود يحتوي على محارف غير مسموحة في المسارات: {code_id!r}")
        elif self._codes.get(code_id, {}).get("is_custom"):
            pass  # custom codes (999-CUS-NNN) bypass the regex — format intentionally differs
        elif not _CODE_ID_PATTERN.match(code_id):
            errors.append(
                f"صيغة الكود غير صالحة: {code_id!r} — المطلوب NNN-XXX-YYY "
                f"(مثال: 003-PIP-SEW)"
            )

    def _check_exists(self, code_id: str, errors: List[str]) -> None:
        if code_id not in self._codes:
            errors.append(f"الكود غير موجود في السجل: {code_id}")

    def _check_active(self, code_id: str, errors: List[str]) -> None:
        code = self._codes[code_id]
        if code.get("status") != "active":
            status = code.get("status", "unknown")
            errors.append(f"الكود غير نشط ({status}): {code_id}")

    def _check_project(self, code_id: str, project_id: str, errors: List[str]) -> None:
        self._check_project_multi(code_id, [project_id], errors)

    def _check_project_multi(self, code_id: str, project_ids: List[str], errors: List[str]) -> None:
        code = self._codes[code_id]
        code_projects = code.get("project_ids", [])
        if not any(pid in code_projects for pid in project_ids):
            errors.append(
                f"الكود {code_id} غير مخصص لأي من المشاريع المختارة — "
                f"المشاريع المتاحة له: {', '.join(code_projects)}. "
                f"الحل: فعّل أحد هذه المشاريع من الأعلى، أو ألغِ تحديد الكود."
            )

    def _check_owner(self, code_id: str, owner_id: str, errors: List[str]) -> None:
        code = self._codes[code_id]
        applicable = code.get("applicable_owners", [])
        if applicable and owner_id not in applicable:
            errors.append(
                f"الكود {code_id} غير مخصص للجهة '{owner_id}' — "
                f"الجهات المقبولة له: {', '.join(applicable)}. "
                f"الحل: بدّل الجهة المالكة، أو ألغِ تحديد الكود."
            )

    def _check_forbidden(
        self, selected_codes: List[str], owner_spec: Dict, errors: List[str]
    ) -> None:
        for code_id in owner_spec.get("forbidden_codes", []):
            if code_id in selected_codes:
                errors.append(f"الكود {code_id} محظور للجهة '{owner_spec.get('owner_id', '?')}'")

    def _check_mandatory(
        self, selected_codes: List[str], owner_spec: Dict, warnings: List[str]
    ) -> None:
        selected_set = set(selected_codes)
        for code_id in owner_spec.get("mandatory_codes", []):
            if code_id not in selected_set:
                warnings.append(
                    f"الكود الإلزامي للجهة '{owner_spec.get('owner_id', '?')}' غير مُضمَّن: {code_id} — "
                    f"أضفه من القائمة، أو تجاهل التحذير إن كان استثناءً مقصوداً."
                )

    def _check_dependencies(
        self,
        selected_codes: List[str],
        project_ids: List[str],
        warnings: List[str],
    ) -> None:
        selected_set = set(selected_codes)
        for code_id in selected_codes:
            code = self._codes.get(code_id)
            if not code:
                continue
            deps = list(code.get("dependencies") or [])
            deps = [
                dep for dep in deps
                if self._dependency_applies_to_projects(dep, project_ids)
            ]
            if self._is_alternative_dependency_set(code, deps):
                if not any(dep in selected_set for dep in deps):
                    warnings.append(
                        f"الكود {code_id} يحتاج إلى أحد الأكواد التالية: {', '.join(deps)} — "
                        f"اضغط «إصلاح تلقائي» لإضافة المناسب."
                    )
                continue
            for dep in deps:
                if dep not in selected_set:
                    warnings.append(
                        f"الكود {code_id} يحتاج إلى {dep} الذي غير موجود في القائمة — "
                        f"اضغط «إصلاح تلقائي» في لوحة المعاينة لإضافته."
                    )

    def _dependency_applies_to_projects(self, dep_code_id: str, project_ids: List[str]) -> bool:
        dep = self._codes.get(dep_code_id)
        if not dep:
            return True
        dep_projects = dep.get("project_ids") or []
        return not dep_projects or any(pid in dep_projects for pid in project_ids)

    def _is_alternative_dependency_set(self, code: Dict, deps: List[str]) -> bool:
        """Delegate to the shared rule — single source of truth (engine/rules.py)."""
        return _rules_alt_deps(self._codes, code, deps)

    # ------------------------------------------------------------------
    # Excavation context (Spec 001)
    # ------------------------------------------------------------------

    # سياقات الحفر المقبولة لكل مشروع — المشروع هو المحدد الأساسي
    _PROJECT_EXCAVATION_CONTEXTS: Dict[str, str] = {
        "wastewater": "infrastructure",
        "water_supply": "infrastructure",
        "water_transmission": "infrastructure",
        "general_construction": "building",
        "asphalt": "road",
        "road_maintenance": "road",
    }

    def _excavation_context_of(self, code_id: str) -> str:
        """Return the excavation context of a code, or '' when not excavation-related."""
        return self._codes.get(code_id, {}).get("excavation_context", "")

    def _check_excavation_context(
        self,
        selected_codes: List[str],
        project_ids: List[str],
        errors: List[str],
        warnings: List[str],
    ) -> None:
        """
        Spec 001 — منع خلط سياقات الحفر المتعارضة داخل عرض واحد.

        القاعدة:
          - كل كود حفر مُصنَّف بسياق (infrastructure / building / road).
          - المشروع المحدد يحدد السياق المقبول الأساسي.
          - خلط سياقين مختلفين من أكواد الحفر في نفس العرض = خطأ يمنع البناء.
          - الكود غير المصنف (excavation_context = '') لا يُمنع، لكنه يُسجَّل
            كتحذير مراجعة (FR-017: لا يُختار صامتاً).
        """
        # 1) تجميع سياقات أكواد الحفر المختارة
        present_contexts: Dict[str, List[str]] = {}
        unclassified: List[str] = []
        for cid in selected_codes:
            ctx = self._excavation_context_of(cid)
            if ctx:
                present_contexts.setdefault(ctx, []).append(cid)
            elif cid.startswith("002-"):
                # كود في فئة الحفر بلا تصنيف سياق → يحتاج مراجعة
                unclassified.append(cid)

        # 2) تعارض داخل العرض: سياقان مختلفان لحفر حقيقي
        if len(present_contexts) > 1:
            contexts_desc = "، ".join(
                f"{ctx} ({', '.join(cids)})"
                for ctx, cids in sorted(present_contexts.items())
            )
            errors.append(
                "تعارض في سياق الحفر: لا يمكن خلط أكثر من سياق حفر واحد في العرض "
                f"({contexts_desc}). الحل: أبقِ نوع حفر واحداً يتوافق مع المشروع المحدد، "
                "أو ألغِ تحديد أكواد السياق الآخر."
            )

        # 3) مطابقة سياق المشروع (تحذير لا خطأ — المشروع قد يكون متعدد النطاقات)
        expected = self._PROJECT_EXCAVATION_CONTEXTS.get(project_ids[0]) if project_ids else None
        if expected and len(present_contexts) == 1:
            only_ctx = next(iter(present_contexts))
            if only_ctx != expected:
                codes_desc = "، ".join(present_contexts[only_ctx])
                warnings.append(
                    f"سياق الحفر المحدد ({only_ctx}) لا يطابق سياق المشروع المتوقع "
                    f"({expected}) — الأكواد: {codes_desc}. تأكد أن نوع الحفر مناسب "
                    "لطبيعة المشروع، أو أضف مشروعاً يبرر هذا السياق."
                )

        # 4) أكواد حفر غير مصنفة → تحذير مراجعة
        if unclassified:
            warnings.append(
                "أكواد حفر بلا تصنيف سياق (تحتاج مراجعة): "
                + "، ".join(unclassified)
                + ". حدّث تصنيفها في السجل قبل الاعتماد النهائي."
            )

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------

    def _load_owner(self, owner_id: str) -> Dict:
        if owner_id in self._owner_cache:
            return self._owner_cache[owner_id]
        path = self._owner_specs_dir / f"{owner_id}.json"
        try:
            spec = load_json(path)
        except (FileNotFoundError, ValueError):
            spec = {"owner_id": owner_id, "mandatory_codes": [], "forbidden_codes": []}
        self._owner_cache[owner_id] = spec
        return spec
