#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Al-Rawaf Technical Proposal Automation System (ATPAS) v1.0
Code Registry Processor & Validator

This module loads codes registry and validates code selections.
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

from utils.json_manager import load_json
from utils.registry_validator import validate_registry

logger = logging.getLogger(__name__)


@dataclass
class CodeInfo:
    """Information about a single code"""
    code_id: str
    activity_name_ar: str
    activity_name_en: str
    project_ids: List[str]
    network_types: List[str]
    applicable_owners: List[str]
    sequence_order: int
    dependencies: List[str]
    page_count: int
    has_images: bool
    image_count: int


class CodesRegistry:
    """Manages the codes registry - SSOT for all codes"""

    def __init__(self, registry_path: str):
        """
        Initialize the registry by loading from JSON file

        Args:
            registry_path: Path to codes_registry.json
        """
        self.registry_path = Path(registry_path)
        self.registry_data = self._load_registry()
        self.codes: Dict[str, Dict] = self.registry_data.get("codes", {})
        self.metadata = self.registry_data.get("metadata", {})

    def _load_registry(self) -> Dict:
        """Load registry from JSON file with schema validation."""
        data = load_json(self.registry_path)
        issues = validate_registry(data)
        for scope, field, message in issues:
            logger.warning("Registry schema issue [%s].%s: %s", scope, field, message)
        return data

    def get_code(self, code_id: str) -> Optional[Dict]:
        """Get a single code by ID"""
        return self.codes.get(code_id)

    def list_codes(self, network_type: str = None, owner: str = None) -> List[str]:
        """
        List all codes, optionally filtered by network type or owner

        Args:
            network_type: Filter by network type (S, W, A)
            owner: Filter by owner (nwc, makkah, moh)

        Returns:
            List of code IDs
        """
        result = []
        for code_id, code_data in self.codes.items():
            if code_data.get("status") != "active":
                continue

            if network_type and network_type not in code_data.get("network_types", []):
                continue

            if owner and owner not in code_data.get("applicable_owners", []):
                continue

            result.append(code_id)

        return sorted(result, key=lambda x: self.codes[x].get("sequence_order", 999))

    def get_dependencies(self, code_id: str) -> List[str]:
        """Get all dependencies for a code"""
        code_data = self.get_code(code_id)
        if not code_data:
            return []
        return code_data.get("dependencies", [])

    def get_all_dependencies(self, code_id: str) -> Set[str]:
        """
        Get all dependencies recursively (transitive closure)

        Args:
            code_id: The code to get dependencies for

        Returns:
            Set of all required code IDs
        """
        visited = set()
        stack = [code_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)
            direct_deps = self.get_dependencies(current)
            stack.extend(direct_deps)

        # Remove the original code from the result
        visited.discard(code_id)
        return visited

    def validate_code_selection(self, selected_codes: List[str], owner: str = None) -> Tuple[bool, List[str]]:
        """
        Validate a selection of codes

        Args:
            selected_codes: List of selected code IDs
            owner: Owner for owner-specific validation

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check if codes exist
        for code_id in selected_codes:
            if code_id not in self.codes:
                errors.append(f"❌ الكود غير موجود: {code_id} (Code not found)")
                continue

            code_data = self.codes[code_id]

            # Check if code is active
            if code_data.get("status") != "active":
                errors.append(f"❌ الكود غير نشط: {code_id} (Code is not active)")

            # Check if owner is applicable
            if owner and owner not in code_data.get("applicable_owners", []):
                errors.append(f"⚠️  الكود {code_id} غير مطبق على الجهة {owner} (Code not applicable to this owner)")

        # Check dependencies
        all_required = set()
        for code_id in selected_codes:
            required = self.get_all_dependencies(code_id)
            missing = required - set(selected_codes)
            if missing:
                missing_str = ", ".join(missing)
                errors.append(f"⚠️  الكود {code_id} يحتاج: {missing_str} (Missing dependencies)")
            all_required.update(required)

        # Check for missing mandatory codes
        mandatory_codes = [cid for cid, data in self.codes.items() 
                          if data.get("status") == "active" and "mandatory" in str(cid).lower()]

        return len(errors) == 0, errors

    def calculate_total_pages(self, selected_codes: List[str]) -> int:
        """Calculate total pages for selected codes"""
        total = 0
        for code_id in selected_codes:
            code_data = self.get_code(code_id)
            if code_data:
                total += code_data.get("page_count", 0)
        return total

    def get_code_info_ar(self, code_id: str) -> str:
        """Get Arabic description of a code"""
        code_data = self.get_code(code_id)
        if not code_data:
            return f"الكود غير موجود: {code_id}"

        name = code_data.get("activity_name_ar", "بدون اسم")
        pages = code_data.get("page_count", 0)
        images = code_data.get("image_count", 0)
        return f"{code_id}: {name} ({pages} صفحة، {images} صورة)"

    def print_summary(self):
        """Print a summary of the registry"""
        print("=" * 60)
        print("📊 نظام تسجيل الأكواد - Code Registry Summary")
        print("=" * 60)
        print(f"الإصدار: {self.metadata.get('version')}")
        print(f"آخر تحديث: {self.metadata.get('last_updated')}")
        print(f"إجمالي الأكواس: {self.metadata.get('total_codes')}")
        print("=" * 60)


class ProposalBuilder:
    """Builds a technical proposal from selected codes"""

    def __init__(self, registry: CodesRegistry, project_id: str, owner: str):
        """
        Initialize builder

        Args:
            registry: CodesRegistry instance
            project_id: Project ID (wastewater, water_supply, asphalt)
            owner: Owner ID (nwc, makkah, moh)
        """
        self.registry = registry
        self.project_id = project_id
        self.owner = owner
        self.selected_codes = []
        self.proposal_data = {}

    def add_code(self, code_id: str) -> bool:
        """
        Add a code to the proposal

        Args:
            code_id: Code to add

        Returns:
            True if successful, False otherwise
        """
        code_data = self.registry.get_code(code_id)
        if not code_data:
            print(f"❌ الكود غير موجود: {code_id}")
            return False

        if code_id in self.selected_codes:
            print(f"⚠️  الكود موجود بالفعل: {code_id}")
            return False

        self.selected_codes.append(code_id)
        return True

    def add_codes_batch(self, codes: List[str]) -> Tuple[int, List[str]]:
        """
        Add multiple codes at once

        Args:
            codes: List of code IDs

        Returns:
            Tuple of (successful_count, failed_codes)
        """
        failed = []
        successful = 0

        for code_id in codes:
            if self.add_code(code_id):
                successful += 1
            else:
                failed.append(code_id)

        return successful, failed

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the selected codes"""
        is_valid, errors = self.registry.validate_code_selection(self.selected_codes, self.owner)
        return is_valid, errors

    def calculate_metrics(self) -> Dict:
        """Calculate proposal metrics"""
        total_pages = self.registry.calculate_total_pages(self.selected_codes)
        total_images = sum(
            self.registry.get_code(code_id).get("image_count", 0)
            for code_id in self.selected_codes
            if self.registry.get_code(code_id)
        )

        return {
            "total_codes": len(self.selected_codes),
            "total_pages": total_pages,
            "total_images": total_images,
            "average_pages_per_code": round(total_pages / len(self.selected_codes), 1) if self.selected_codes else 0
        }

    def generate_report(self) -> str:
        """Generate a text report of the proposal"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("📋 تقرير الاقتراح الفني - Technical Proposal Report")
        report_lines.append("=" * 70)
        report_lines.append(f"")
        report_lines.append(f"المشروع: {self.project_id} | الجهة المالكة: {self.owner}")
        report_lines.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        is_valid, errors = self.validate()
        metrics = self.calculate_metrics()

        report_lines.append("📊 المقاييس:")
        report_lines.append(f"  • عدد الأكواد: {metrics['total_codes']}")
        report_lines.append(f"  • إجمالي الصفحات: {metrics['total_pages']}")
        report_lines.append(f"  • إجمالي الصور: {metrics['total_images']}")
        report_lines.append(f"  • متوسط الصفحات لكل كود: {metrics['average_pages_per_code']}")
        report_lines.append("")

        report_lines.append("✅ الأكواد المختارة:")
        for i, code_id in enumerate(sorted(self.selected_codes), 1):
            info = self.registry.get_code_info_ar(code_id)
            report_lines.append(f"  {i}. {info}")
        report_lines.append("")

        if errors:
            report_lines.append(f"⚠️  تحذيرات ({len(errors)}):")
            for error in errors:
                report_lines.append(f"  • {error}")
            report_lines.append("")
        else:
            report_lines.append("✅ لا توجد مشاكل - جميع الأكواد صحيحة")
            report_lines.append("")

        report_lines.append("=" * 70)
        return "\n".join(report_lines)

    def print_report(self):
        """Print the proposal report"""
        print(self.generate_report())


# ============================================================================
# Demo / Test Function
# ============================================================================

def demo_usage():
    """Demonstrate usage of the system"""
    print("\n🚀 نظام الأتمتة الذكي للعروض الفنية")
    print("Al-Rawaf Technical Proposal Automation System v1.0")
    print("-" * 70)

    # Load registry
    print("\n📚 تحميل سجل الأكواس...")
    registry = CodesRegistry("codes_registry.json")
    registry.print_summary()

    # Show available codes for wastewater project
    print("\n📋 الأكواس المتاحة لمشروع الصرف الصحي:")
    available_codes = registry.list_codes(network_type="S", owner="nwc")
    for i, code_id in enumerate(available_codes, 1):
        print(f"  {i}. {registry.get_code_info_ar(code_id)}")

    # Build a proposal
    print("\n🏗️  بناء عرض فني تجريبي...")
    builder = ProposalBuilder(registry, "wastewater", "nwc")

    # Add codes for a small network
    codes_to_add = [
        "001-SUR-BASE",
        "001-PRM-GOV",
        "001-APP-DES",
        "001-APP-HSE",
        "002-MAT-SITE",
        "002-EXC-FINE",
        "002-WST-EXC",
        "003-PIP-SEW",
        "004-TST-LEK",
        "005-BKF-SND",
        "005-BKF-SOL",
        "005-RST-ASP",
        "005-HND-DOC",
        "005-HND-FIN"
    ]

    successful, failed = builder.add_codes_batch(codes_to_add)
    print(f"✅ تم إضافة {successful} أكواد بنجاح")
    if failed:
        print(f"❌ فشل إضافة {len(failed)} أكواد: {', '.join(failed)}")

    # Generate report
    print("\n" + builder.generate_report())


if __name__ == "__main__":
    demo_usage()
