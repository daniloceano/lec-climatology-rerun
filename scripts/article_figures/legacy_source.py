"""Load plotting definitions from the frozen manuscript source without side effects.

Several article scripts execute data reads at import time.  This loader keeps
their imports, constants, functions and classes, while deliberately omitting
the top-level execution statements.  It lets the corrected workflow call the
actual publication renderers without modifying the archived manuscript tree.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


def load_definitions(path: Path, *, skip_imports: set[str] | None = None) -> SimpleNamespace:
    skip_imports = skip_imports or set()
    tree = ast.parse(path.read_text(), filename=str(path))
    selected: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in skip_imports for alias in node.names):
                continue
            selected.append(node)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in skip_imports:
                continue
            selected.append(node)
        elif isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            selected.append(node)

    module = ast.Module(body=selected, type_ignores=[])
    namespace: dict = {"__file__": str(path), "__name__": f"legacy_{path.stem}"}
    exec(compile(module, str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)
