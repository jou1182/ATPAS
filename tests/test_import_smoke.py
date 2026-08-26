#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Import-smoke test: every module under ui/ and utils/ and engine/ must import.

Catches runtime NameErrors and broken module-level references that compileall
cannot see (e.g. a file using `theme.X` without importing the theme module —
the exact bug that silently killed the frozen EXE at startup).

Run:
    python -m pytest tests/test_import_smoke.py -v
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.mark.parametrize("package", ["ui", "utils", "engine"])
def test_every_module_imports(package: str) -> None:
    pkg_dir = ROOT / package
    modules = sorted(p.stem for p in pkg_dir.glob("*.py") if p.stem != "__init__")
    assert modules, f"no modules found under {package}"
    for name in modules:
        mod_name = f"{package}.{name}"
        try:
            importlib.import_module(mod_name)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"importing {mod_name} failed: {type(exc).__name__}: {exc}")


def test_theme_module_importable_everywhere_it_is_used() -> None:
    """Static guard: any ui file referencing `theme.X` must import the module."""
    import re

    uses = re.compile(r"\btheme\.[A-Za-z_]")
    has_import = re.compile(
        r"^\s*from\s+ui\s+import\s+[^\n]*\btheme\b|^\s*from\s+ui\.theme\s+import\s+[^\n]*[\s(,]theme[\s,)\n]|^\s*import\s+ui\.theme(?:\s+as\s+theme)?",
        re.MULTILINE,
    )

    def _strip_noncode(src: str) -> str:
        """احذف docstrings ثم التعليقات — الحارس يفحص الكود الفعلي فقط."""
        src = re.sub(r'"""[\s\S]*?"""', " ", src)
        src = re.sub(r"'''[\s\S]*?'''", " ", src)
        return "\n".join(
            line.split("#", 1)[0] for line in src.splitlines()
        )

    for py in sorted((ROOT / "ui").glob("*.py")):
        if py.name == "theme.py":
            continue
        code_only = _strip_noncode(py.read_text(encoding="utf-8"))
        if uses.search(code_only) and not has_import.search(py.read_text(encoding="utf-8")):
            pytest.fail(f"{py.name} uses theme.* without 'from ui import theme'")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
