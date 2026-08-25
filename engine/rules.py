#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""قواعد مشتركة بين Validator و DependencyResolver.

المصدر الوحيد لمنطق «مجموعة التبعيات البديلة» — أي مجموعة تبعيات يُكتفى فيها
بتحقيق أحد الأكواد بدلاً من كلها (مثال: طرق حفر متعددة لمقطوعات مختلفة).

هذا المنطق كان مكرراً في engine/validator.py و engine/dependency_resolver.py؛
أي تعديل مستقبلي يُجرى هنا فقط حتى لا تنحرف القواعد بين الطبقتين.
"""

from __future__ import annotations

from typing import Dict, List, Mapping


def is_alternative_dependency_set(
    codes: Mapping[str, Dict],
    code: Dict,
    deps: List[str],
) -> bool:
    """حدد إن كانت قائمة التبعيات *deps* بديلة (any-of) لا إلزامية (all-of).

    القواعد:
      1. أقل من تبعيتين ⇒ ليست بديلة.
      2. ملاحظة التبعيات تحوي «أي» أو "any" ⇒ بديلة.
      3. كل التبعيات تحمل excavation_type (طرق حفر متعددة مقبولة) ⇒ بديلة.
      4. مجموعات مشاريع التبعيات منفصلة تماماً عن بعضها ⇒ بديلة
         (كل تبعية تخص مشروعاً لا يشاركها غيرها).

    Args:
        codes: سجل الأكواد الكامل ({code_id: entry}).
        code:  مدخل الكود صاحب التبعيات.
        deps:  قائمة معرفات التبعيات.

    Returns:
        True إذا كانت المجموعة بديلة.
    """
    if len(deps) < 2:
        return False

    note = str(code.get("dependencies_note", ""))
    if "أي" in note or "any" in note.lower():
        return True

    dep_records = [codes.get(dep, {}) for dep in deps]
    if dep_records and all("excavation_type" in dep for dep in dep_records):
        return True

    project_sets = [
        set(dep.get("project_ids") or [])
        for dep in dep_records
        if dep.get("project_ids")
    ]
    if len(project_sets) == len(deps):
        for idx, current in enumerate(project_sets):
            others = set().union(*(s for j, s in enumerate(project_sets) if j != idx))
            if current & others:
                return False
        return True

    return False
