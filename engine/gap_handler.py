#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from utils.json_manager import load_json, save_json


class GapHandler:
    """
    ينشئ أكواداً جديدة (CUSTOM-NNN) للبنود غير الموجودة في السجل.

    Usage:
        handler = GapHandler("codes_registry.json")
        code_id = handler.create("حفر خاص", "wastewater")
        # code_id = "CUSTOM-001"
    """

    def __init__(self, registry_path: str | Path = "codes_registry.json") -> None:
        self._registry_path = Path(registry_path)

    def _next_id(self, codes: dict) -> str:
        existing = [k for k in codes if k.startswith("CUSTOM-")]
        if not existing:
            return "CUSTOM-001"
        numbers = [int(k.split("-")[1]) for k in existing]
        return f"CUSTOM-{max(numbers) + 1:03d}"

    def create(self, boq_item: str, project_type: str) -> str:
        """
        ينشئ كود جديد في codes_registry.json ويُرجع الـ code_id.

        Args:
            boq_item: اسم البند من جدول الكميات
            project_type: نوع المشروع (مثلاً "wastewater")

        Returns:
            str — الـ code_id الجديد (مثلاً "CUSTOM-001")
        """
        registry = load_json(self._registry_path)
        codes = registry.setdefault("codes", {})
        code_id = self._next_id(codes)

        codes[code_id] = {
            "code_id": code_id,
            "category": "CUSTOM",
            "phase": "GEN",
            "variation": f"{len(codes):03d}",
            "activity_name_ar": boq_item,
            "activity_name_en": boq_item,
            "project_ids": [project_type],
            "network_types": [],
            "applicable_owners": [],
            "sequence_order": 999,
            "dependencies": [],
            "status": "active",
            "is_custom": True,
        }

        save_json(registry, self._registry_path)
        return code_id
