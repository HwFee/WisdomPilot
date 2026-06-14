#!/usr/bin/env python3
"""
Scan TypeScript/TSX codebase for structural issues per AGENTS.md.
Uses regex-based heuristics (no TS parser dependency).
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

WARN_LENGTH = 40
CRIT_LENGTH = 80
WARN_DEPTH = 4
WARN_FILE = 400
CRIT_FILE = 800

SUSPICIOUS_NAMES = {
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    "tmp", "temp", "cnt", "num", "val", "var", "usr", "uid", "idx",
    "arr", "lst", "dict", "obj", "ctx", "req", "res", "resp", "err",
    "msg", "str", "int", "flt", "bool", "fn", "func", "cb",
}

MAGIC_NUMBER_WHITELIST = {"0", "1", "-1", "0.0", "1.0", "-1.0", "''", '""', "true", "false", "null", "undefined"}

# Regex patterns
FUNC_START_RE = re.compile(
    r'^(?:\s*(?:async\s+)?function\s+\w+|\s*\w+\s*\([^)]*\)\s*[{=>]|\s*\w+\s*:\s*(?:async\s+)?(?:function)?\s*\([^)]*\)\s*[{=>]|\s*(?:get|set|async)\s+\w+\s*\([^)]*\)\s*\{)',
    re.IGNORECASE,
)
ARROW_FUNC_RE = re.compile(r'=>\s*\{')
CONST_LET_VAR_RE = re.compile(r'(?:const|let|var)\s+(\w+)')
MAGIC_NUM_RE = re.compile(r'(?<![\w"\'])(-?\d+\.?\d*)(?![\w"\'])')
MAGIC_STR_RE = re.compile(r'["\']([^"\']{2,})["\']')
NEST_RE = re.compile(r'^\s*(?:if|for|while|switch|catch)\s*[\(\{]')


@dataclass
class Issue:
    file: str
    line: int
    col: int
    severity: str
    category: str
    message: str
    context: str = ""


def scan_file(filepath: Path) -> List[Issue]:
    issues: List[Issue] = []
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return [Issue(file=str(filepath), line=0, col=0, severity="warn", category="parse", message=f"Read error: {e}")]

    total_lines = len(lines)
    if total_lines > CRIT_FILE:
        issues.append(Issue(
            file=str(filepath), line=1, col=0, severity="crit", category="file_length",
            message=f"File is {total_lines} lines (>{CRIT_FILE})",
        ))
    elif total_lines > WARN_FILE:
        issues.append(Issue(
            file=str(filepath), line=1, col=0, severity="warn", category="file_length",
            message=f"File is {total_lines} lines (>{WARN_FILE})",
        ))

    # Track brace balance to estimate function boundaries
    brace_stack = []
    func_start_line = None
    func_name = None
    max_nesting_in_func = 0
    current_nesting = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith('//') or stripped.startswith('*') or stripped.startswith('/*'):
            continue

        # Detect function start
        if FUNC_START_RE.match(line) or ARROW_FUNC_RE.search(line):
            if not brace_stack:
                func_start_line = i
                # Try to extract name
                m = re.search(r'function\s+(\w+)', line)
                if m:
                    func_name = m.group(1)
                else:
                    m = re.search(r'(\w+)\s*[:\(]', line)
                    func_name = m.group(1) if m else "anonymous"
                max_nesting_in_func = 0
                current_nesting = 0

        # Track braces
        for ch in line:
            if ch == '{':
                brace_stack.append(i)
            elif ch == '}':
                if brace_stack:
                    brace_stack.pop()
                    if not brace_stack and func_start_line is not None:
                        body_lines = i - func_start_line - 1
                        if body_lines > CRIT_LENGTH:
                            issues.append(Issue(
                                file=str(filepath), line=func_start_line, col=0,
                                severity="crit", category="length",
                                message=f"Function '{func_name}' body ≈{body_lines} lines (>{CRIT_LENGTH})",
                            ))
                        elif body_lines > WARN_LENGTH:
                            issues.append(Issue(
                                file=str(filepath), line=func_start_line, col=0,
                                severity="warn", category="length",
                                message=f"Function '{func_name}' body ≈{body_lines} lines (>{WARN_LENGTH})",
                            ))
                        if max_nesting_in_func > WARN_DEPTH:
                            issues.append(Issue(
                                file=str(filepath), line=func_start_line, col=0,
                                severity="warn", category="depth",
                                message=f"Function '{func_name}' max nesting depth ≈{max_nesting_in_func} (>{WARN_DEPTH})",
                            ))
                        func_start_line = None
                        func_name = None

        # Nesting depth inside function
        if func_start_line is not None and brace_stack:
            if NEST_RE.match(line):
                current_nesting = len(brace_stack)
                max_nesting_in_func = max(max_nesting_in_func, current_nesting)

        # Naming
        for m in CONST_LET_VAR_RE.finditer(line):
            name = m.group(1)
            if name in SUSPICIOUS_NAMES:
                issues.append(Issue(
                    file=str(filepath), line=i, col=m.start(),
                    severity="warn", category="naming",
                    message=f"Suspicious variable name '{name}'",
                    context=line.strip(),
                ))

        # Magic numbers (skip if looks like assignment RHS with named LHS)
        is_assignment_rhs = False
        if '=' in line and not any(op in line for op in ('==', '===', '!=', '!==', '>=', '<=', '=>')):
            parts = line.split('=')
            if len(parts) >= 2:
                lhs = parts[0].strip()
                if lhs and not lhs.startswith('//') and re.match(r'^[a-zA-Z_]\w*$', lhs.split()[-1]):
                    is_assignment_rhs = True

        if not is_assignment_rhs:
            for m in MAGIC_NUM_RE.finditer(line):
                val = m.group(1)
                if val.lower() not in MAGIC_NUMBER_WHITELIST:
                    issues.append(Issue(
                        file=str(filepath), line=i, col=m.start(),
                        severity="warn", category="magic",
                        message=f"Magic number: {val}",
                        context=line.strip(),
                    ))

            for m in MAGIC_STR_RE.finditer(line):
                val = m.group(1)
                # Skip obvious non-magic: URLs, file paths, class names, error messages in raises
                if len(val) >= 2 and not val.isupper() and not re.match(r'^https?://', val):
                    issues.append(Issue(
                        file=str(filepath), line=i, col=m.start(),
                        severity="warn", category="magic",
                        message=f"Magic string: '{val[:40]}{'...' if len(val) > 40 else ''}'",
                        context=line.strip(),
                    ))

    return issues


def main():
    root = Path(__file__).parent.parent / "frontend"
    issues: List[Issue] = []

    for dirpath, _, filenames in os.walk(root):
        if "node_modules" in dirpath or ".next" in dirpath:
            continue
        for fname in filenames:
            if fname.endswith(".ts") or fname.endswith(".tsx"):
                fpath = Path(dirpath) / fname
                if fpath.exists():
                    issues.extend(scan_file(fpath))

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

    for cat in ("length", "depth", "magic", "naming", "file_length", "parse"):
        count = sum(1 for i in issues if i.category == cat)
        if count:
            output["summary"]["by_category"][cat] = count

    out_path = Path(__file__).parent.parent / "reports" / "ts-issues.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Scan complete: {len(issues)} issues found")
    print(f"  Critical: {output['summary']['crit']}")
    print(f"  Warning:  {output['summary']['warn']}")
    print(f"  By category: {output['summary']['by_category']}")
    print(f"  Output: {out_path}")


if __name__ == "__main__":
    main()
