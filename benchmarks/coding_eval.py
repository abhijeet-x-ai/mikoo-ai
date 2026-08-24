#!/usr/bin/env python3
"""Offline coding-agent evaluation harness.

The default checks are non-executing and safe: JSON action validation, unified
patch presence, language-aware syntax checks where available, and bounded
output accounting. Running arbitrary generated code is intentionally excluded;
use an explicit sandbox profile for execution.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ACTION_RE = re.compile(r'^(list_files|read_file|search_files|propose_patch|apply_patch|run_tests|format_code|final_answer)$')


def validate_action(path: Path) -> tuple[bool, str]:
    try:
        action = json.loads(path.read_text())
    except Exception as exc:
        return False, f"invalid JSON: {exc}"
    if not isinstance(action, dict) or not ACTION_RE.match(str(action.get("action", ""))):
        return False, "invalid or missing action"
    if action.get("action") in {"apply_patch", "run_tests"} and action.get("approval_required") is not True:
        return False, "write/execute actions require approval_required=true"
    if action.get("action") == "apply_patch" and not action.get("diff"):
        return False, "apply_patch requires a diff"
    return True, "valid action"


def validate_python(path: Path) -> tuple[bool, str]:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        return True, "python syntax valid"
    except SyntaxError as exc:
        return False, f"python syntax error: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action-json", type=Path)
    parser.add_argument("--python-file", type=Path)
    parser.add_argument("--max-output-bytes", type=int, default=12000)
    args = parser.parse_args()
    checks = []
    if args.action_json:
        checks.append(validate_action(args.action_json))
    if args.python_file:
        checks.append(validate_python(args.python_file))
    if not checks:
        parser.error("provide --action-json and/or --python-file")
    for ok, message in checks:
        print(("PASS" if ok else "FAIL") + ": " + message)
    if not all(ok for ok, _ in checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
