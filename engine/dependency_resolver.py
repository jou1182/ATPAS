#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Set

from engine.rules import is_alternative_dependency_set
from engine.types import CodeRegistry
from utils.json_manager import load_json


class DependencyResolver:
    """
    Resolves transitive dependency closures for selected codes.

    Usage:
        resolver = DependencyResolver(codes)       # codes = registry["codes"]
        full_set = resolver.resolve(["003-PIP-SEW"])
        gaps     = resolver.suggest_missing(["003-PIP-SEW", "002-EXC-FINE"])
    """

    def __init__(self, codes: CodeRegistry) -> None:
        if not isinstance(codes, dict):
            raise TypeError(
                f"codes must be a dict[str, dict], got {type(codes).__name__}"
            )
        self._codes: CodeRegistry = codes

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, selected_codes: List[str]) -> List[str]:
        """
        Return the complete set of codes required to satisfy all dependencies,
        sorted by sequence_order.

        Includes every code in selected_codes plus any missing prerequisites
        found by walking the dependency graph.
        """
        full: Set[str] = set()
        for code_id in selected_codes:
            self._walk(code_id, full)
        return self._sorted(full)

    def suggest_missing(self, selected_codes: List[str]) -> List[str]:
        """
        Return only the codes that are required by selected_codes but not
        currently in the selection.
        """
        full = set(self.resolve(selected_codes))
        current = set(selected_codes)
        missing = full - current
        return self._sorted(missing)

    def dependencies_of(self, code_id: str) -> List[str]:
        """Return direct (non-transitive) dependencies of a single code."""
        code = self._codes.get(code_id)
        if not code:
            return []
        return list(code.get("dependencies") or [])

    def resolve_with_order(
        self,
        selected_codes: List[str],
        boq_order: List[str],
    ) -> List[str]:
        """Return codes in BOQ order, injecting missing dependencies just before
        the first code that needs them.

        Args:
            selected_codes: All codes the user selected (superset of boq_order).
            boq_order:      Codes in the tender's BOQ sequence.

        Returns:
            Ordered list — BOQ sequence preserved, missing deps injected in place,
            extra selected codes appended at end sorted by sequence_order.
        """
        if not boq_order:
            return []

        # 1. Compute full required set (transitive deps of all selected codes)
        full_required: Set[str] = set()
        for code_id in selected_codes:
            self._walk(code_id, full_required)

        # 2. Extras = required but NOT explicitly in boq_order
        boq_set = {c for c in boq_order if c in self._codes}
        extras: Set[str] = full_required - boq_set

        # 3. Build result — walk BOQ order, inject extras before their consumer
        result: List[str] = []
        placed: Set[str] = set()
        selected_set: Set[str] = set(selected_codes)

        for code_id in boq_order:
            if code_id not in self._codes:
                continue  # unknown code — skip silently
            if code_id not in selected_set:
                continue  # user explicitly deselected — honour their choice
            self._inject_deps(code_id, extras, placed, result)
            if code_id not in placed:
                result.append(code_id)
                placed.add(code_id)

        # 4. Append remaining extras sorted by sequence_order
        remaining = [c for c in self._sorted(full_required) if c not in placed]
        result.extend(remaining)

        return result

    def _inject_deps(
        self,
        code_id: str,
        extras: Set[str],
        placed: Set[str],
        result: List[str],
    ) -> None:
        """Recursively place transitive dependencies from *extras* before code_id."""
        for dep in (self._codes.get(code_id, {}).get("dependencies") or []):
            if dep in extras and dep not in placed:
                self._inject_deps(dep, extras, placed, result)
                result.append(dep)
                placed.add(dep)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _walk(self, code_id: str, visited: Set[str]) -> None:
        """DFS walk — add code_id and all its transitive dependencies to visited."""
        if code_id in visited:
            return
        if code_id not in self._codes:
            return
        visited.add(code_id)
        for dep in self._effective_dependencies(code_id, visited):
            self._walk(dep, visited)

    def _effective_dependencies(self, code_id: str, selected_or_visited: Set[str]) -> List[str]:
        """Return dependencies still needed, honoring alternative dependency lists."""

        code = self._codes.get(code_id, {})
        deps = list(code.get("dependencies") or [])
        if not deps or not self._is_alternative_dependency_set(code, deps):
            return deps

        if any(dep in selected_or_visited for dep in deps):
            return []
        return [deps[0]]

    def _is_alternative_dependency_set(self, code: Dict, deps: List[str]) -> bool:
        """Delegate to the shared rule — single source of truth (engine/rules.py)."""
        return is_alternative_dependency_set(self._codes, code, deps)

    def _sorted(self, code_ids: Set[str] | List[str]) -> List[str]:
        """Sort codes by their sequence_order, unknown codes go last."""
        def order_key(cid: str) -> int:
            code = self._codes.get(cid)
            return code.get("sequence_order", 9999) if code else 9999

        return sorted(code_ids, key=order_key)
