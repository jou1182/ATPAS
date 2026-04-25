#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from pathlib import Path
from typing import Dict, List, Tuple

from engine.types import CodeRegistry
from utils.json_manager import load_json

# Codes with this field belong to a mutually-exclusive excavation group
_EXC_FIELD = "excavation_type"

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
        self._check_exclusive_groups(selected_codes, errors)
        self._check_mandatory(selected_codes, owner_spec, warnings)
        self._check_dependencies(selected_codes, warnings)

        return len(errors) == 0, errors, warnings

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_format(self, code_id: str, errors: List[str]) -> None:
        """Reject malformed or potentially unsafe code IDs before any filesystem use."""
        if any(ch in code_id for ch in ("/", "\\", "..", "~", "\x00")):
            errors.append(f"الكود يحتوي على محارف غير مسموحة في المسارات: {code_id!r}")
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
                f"المشاريع المتاحة: {', '.join(code_projects)}"
            )

    def _check_owner(self, code_id: str, owner_id: str, errors: List[str]) -> None:
        code = self._codes[code_id]
        applicable = code.get("applicable_owners", [])
        if applicable and owner_id not in applicable:
            errors.append(
                f"الكود {code_id} غير مخصص للجهة '{owner_id}' — "
                f"الجهات المتاحة: {', '.join(applicable)}"
            )

    def _check_forbidden(
        self, selected_codes: List[str], owner_spec: Dict, errors: List[str]
    ) -> None:
        for code_id in owner_spec.get("forbidden_codes", []):
            if code_id in selected_codes:
                errors.append(f"الكود {code_id} محظور للجهة '{owner_spec.get('owner_id', '?')}'")

    def _check_exclusive_groups(self, selected_codes: List[str], errors: List[str]) -> None:
        """Ensure at most one excavation type is selected."""
        exc_codes = [
            c for c in selected_codes
            if c in self._codes and _EXC_FIELD in self._codes[c]
        ]
        if len(exc_codes) > 1:
            names = [
                f"{c} ({self._codes[c].get(_EXC_FIELD, '')})"
                for c in exc_codes
            ]
            errors.append(
                f"لا يمكن اختيار أكثر من نوع حفر واحد في نفس الوقت: {', '.join(names)}"
            )

    def _check_mandatory(
        self, selected_codes: List[str], owner_spec: Dict, warnings: List[str]
    ) -> None:
        selected_set = set(selected_codes)
        for code_id in owner_spec.get("mandatory_codes", []):
            if code_id not in selected_set:
                warnings.append(
                    f"الكود الإلزامي للجهة '{owner_spec.get('owner_id', '?')}' غير مُضمَّن: {code_id}"
                )

    def _check_dependencies(self, selected_codes: List[str], warnings: List[str]) -> None:
        selected_set = set(selected_codes)
        for code_id in selected_codes:
            code = self._codes.get(code_id)
            if not code:
                continue
            for dep in code.get("dependencies", []):
                if dep not in selected_set:
                    warnings.append(
                        f"الكود {code_id} يحتاج إلى {dep} الذي غير موجود في القائمة"
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
