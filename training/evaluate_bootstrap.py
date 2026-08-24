#!/usr/bin/env python3
"""Small deterministic acceptance evaluation for Mikoo Nano bootstrap behavior."""
from __future__ import annotations

import argparse

from test_bootstrap_generation import generate, load


CASES = [
    ("Hello", ["Hello", "Mikoo"]),
    ("Fix a bug in my selected file", ["fix", "patch"]),
    ("Write tests for this function", ["function", "contract"]),
    ("Review this function", ["review", "check"]),
    ("বাংলায় বলো", ["Mikoo", "অফলাইনে"]),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    args = parser.parse_args()
    arrays = load(args.checkpoint)
    failures = []
    for prompt, expected in CASES:
        response = generate(arrays, prompt)
        normalized = response.casefold()
        missing = [term for term in expected if term.casefold() not in normalized]
        print(f"prompt={prompt!r} response={response!r}")
        if missing:
            failures.append((prompt, missing))
    if failures:
        raise SystemExit(f"bootstrap evaluation failed: {failures}")
    print(f"bootstrap evaluation passed: {len(CASES)} cases")


if __name__ == "__main__":
    main()
