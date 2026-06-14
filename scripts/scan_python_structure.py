#!/usr/bin/env python3
"""
Scan Python codebase for structural issues per AGENTS.md:
- Function length (>40 warn, >80 critical)
- Nesting depth (>4 warn)
- Magic numbers/strings
- Suspicious naming (single-letter, abbreviations)
"""

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

WARN_LENGTH = 40
CRIT_LENGTH = 80
WARN_DEPTH = 4

SUSPICIOUS_NAMES = {
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "tmp", "temp", "cnt", "num", "val", "var", "usr", "uid", "idx",
    "arr", "lst", "dict", "obj", "ctx", "req", "res", "resp", "err",
    "msg", "str", "int", "flt", "bool", "fn", "func", "cb",
}

MAGIC_NUMBER_WHITELIST = {0, 1, -1, 0.0, 1.0, -1.0, "", " "}


@dataclass
class Issue:
    file: str
    line: int
    col: int
    severity: str  # warn / crit
    category: str  # length / depth / magic / naming
    message: str
    context: str = ""


def get_function_body_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count effective lines in function body (excluding docstring)."""
    if not node.body:
        return 0
    start = node.body[0].lineno
    # Skip docstring
    if (
        isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, (ast.Str, ast.Constant))
    ):
        if len(node.body) > 1:
            start = node.body[1].lineno
        else:
            return 0
    end = node.body[-1].end_lineno if hasattr(node.body[-1], "end_lineno") else node.body[-1].lineno
    return end - start + 1


def max_nesting_depth(node: ast.AST) -> int:
    """Return max nesting depth of if/for/while/try/with/asyncfor inside a node."""
    nest_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.ExceptHandler)

    def dfs(n: ast.AST, depth: int) -> int:
        max_d = depth if isinstance(n, nest_nodes) else 0
        for child in ast.iter_child_nodes(n):
            child_max = dfs(child, depth + (1 if isinstance(child, nest_nodes) else 0))
            max_d = max(max_d, child_max)
        return max_d

    return dfs(node, 0)


def is_magic_number(node: ast.Constant) -> bool:
    val = node.value
    if val in MAGIC_NUMBER_WHITELIST:
        return False
    if isinstance(val, (int, float)) and val in MAGIC_NUMBER_WHITELIST:
        return False
    if isinstance(val, (int, float)):
        return True
    if isinstance(val, str) and len(val) >= 2 and not val.isupper():
        return True
    return False


class ScanVisitor(ast.NodeVisitor):
    def __init__(self, filepath: Path, source: str):
        self.issues: List[Issue] = []
        self.filepath = filepath
        self.source = source
        self.lines = source.splitlines()
        self._current_func = None
        self._parent = None
        self._grandparent = None

    def visit_FunctionDef(self, node):
        old_func = self._current_func
        self._current_func = node
        body_lines = get_function_body_lines(node)
        if body_lines > CRIT_LENGTH:
            self.issues.append(Issue(
                file=str(self.filepath), line=node.lineno, col=node.col_offset,
                severity="crit", category="length",
                message=f"Function '{node.name}' body is {body_lines} lines (>{CRIT_LENGTH})",
                context=f"def {node.name}(...)",
            ))
        elif body_lines > WARN_LENGTH:
            self.issues.append(Issue(
                file=str(self.filepath), line=node.lineno, col=node.col_offset,
                severity="warn", category="length",
                message=f"Function '{node.name}' body is {body_lines} lines (>{WARN_LENGTH})",
                context=f"def {node.name}(...)",
            ))
        depth = max_nesting_depth(node)
        if depth > WARN_DEPTH:
            self.issues.append(Issue(
                file=str(self.filepath), line=node.lineno, col=node.col_offset,
                severity="warn", category="depth",
                message=f"Function '{node.name}' max nesting depth is {depth} (>{WARN_DEPTH})",
                context=f"def {node.name}(...)",
            ))
        self.generic_visit(node)
        self._current_func = old_func

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store) and node.id in SUSPICIOUS_NAMES:
            self.issues.append(Issue(
                file=str(self.filepath), line=node.lineno, col=node.col_offset,
                severity="warn", category="naming",
                message=f"Suspicious variable name '{node.id}'",
                context=f"{node.id} = ...",
            ))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if is_magic_number(node) and not self._is_assigned_value(node) and not self._is_docstring(node):
            self.issues.append(Issue(
                file=str(self.filepath), line=node.lineno, col=node.col_offset,
                severity="warn", category="magic",
                message=f"Magic literal: {repr(node.value)}",
                context=self.lines[node.lineno - 1].strip() if node.lineno <= len(self.lines) else "",
            ))
        self.generic_visit(node)

    def _is_docstring(self, node: ast.Constant) -> bool:
        if not isinstance(node.value, str):
            return False
        if isinstance(self._parent, ast.Expr):
            return True
        return False

    def _is_assigned_value(self, node: ast.Constant) -> bool:
        """Check if this constant is the RHS of a simple assignment (x = ...)."""
        if self._parent is None:
            return False
        if isinstance(self._parent, ast.Assign):
            return self._parent.value is node
        if isinstance(self._parent, ast.AnnAssign) and self._parent.value is node:
            return True
        return False

    def generic_visit(self, node):
        old_parent = self._parent
        self._parent = node
        super().generic_visit(node)
        self._parent = old_parent


def scan_file(filepath: Path) -> List[Issue]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return [Issue(
            file=str(filepath), line=0, col=0,
            severity="warn", category="parse",
            message=f"Parse error: {e}",
        )]

    visitor = ScanVisitor(filepath, source)
    visitor.visit(tree)
    return visitor.issues


def main():
    root = Path(__file__).parent.parent / "backend"
    issues: List[Issue] = []

    for pyfile in root.rglob("*.py"):
        if "__pycache__" in str(pyfile) or ".pytest_cache" in str(pyfile):
            continue
        issues.extend(scan_file(pyfile))

    output = {
        "scan_target": str(root),
        "total_issues": len(issues),
        "summary": {
            "crit": sum(1 for i in issues if i.severity == "crit"),
            "warn": sum(1 for i in issues if i.severity == "warn"),
            "by_category": {},
        },
        "issues": [asdict(i) for i in issues],
    }

    for cat in ("length", "depth", "magic", "naming", "parse"):
        count = sum(1 for i in issues if i.category == cat)
        if count:
            output["summary"]["by_category"][cat] = count

    out_path = Path(__file__).parent.parent / "reports" / "python-issues.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scan complete: {len(issues)} issues found")
    print(f"  Critical: {output['summary']['crit']}")
    print(f"  Warning:  {output['summary']['warn']}")
    print(f"  By category: {output['summary']['by_category']}")
    print(f"  Output: {out_path}")


if __name__ == "__main__":
    main()
