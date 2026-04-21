#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Set

from utils.json_manager import load_json


class DependencyResolver:
    """
    Resolves transitive dependency closures for selected codes.

    Usage:
        resolver = DependencyResolver(codes)       # codes = registry["codes"]
        full_set = resolver.resolve(["003-PIP-SEW"])
        gaps     = resolver.suggest_missing(["003-PIP-SEW", "002-EXC-FINE"])
    """

    def __init__(self, codes: Dict[str, Dict]):
        self._codes = codes

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
        return list(code.get("dependencies", []))

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
        for dep in self._codes[code_id].get("dependencies", []):
            self._walk(dep, visited)

    def _sorted(self, code_ids: Set[str] | List[str]) -> List[str]:
        """Sort codes by their sequence_order, unknown codes go last."""
        def order_key(cid: str) -> int:
            code = self._codes.get(cid)
            return code.get("sequence_order", 9999) if code else 9999

        return sorted(code_ids, key=order_key)
