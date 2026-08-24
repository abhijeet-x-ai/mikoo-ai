#!/usr/bin/env python3
"""Pack cleaned JSONL text into a streamable uint8 token array.

This is the dependency-light byte-token path used for smoke training and
pipeline validation. Production Mikoo should replace it with the selected
24,576-token tokenizer after tokenizer evaluation, while keeping the same
manifest and provenance boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SEPARATOR = b"\n<|end|>\n"


def records(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            value = json.loads(line)
            text = value.get("text") if isinstance(value, dict) else None
            if isinstance(text, str) and text:
                yield text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=0)
    args = parser.parse_args()

    total = 0
    count = 0
    for text in records(args.input):
        total += len(text.encode("utf-8")) + len(SEPARATOR)
        count += 1
    if total < 2:
        raise SystemExit("no usable text records")
    if args.max_bytes > 0 and total > args.max_bytes:
        raise SystemExit(f"packed corpus would be {total} bytes, above --max-bytes={args.max_bytes}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    packed = np.lib.format.open_memmap(args.output, mode="w+", dtype=np.uint8, shape=(total,))
    position = 0
    digest = hashlib.sha256()
    for text in records(args.input):
        data = text.encode("utf-8") + SEPARATOR
        packed[position : position + len(data)] = np.frombuffer(data, dtype=np.uint8)
        digest.update(data)
        position += len(data)
    packed.flush()
    manifest = {
        "input": str(args.input),
        "output": str(args.output),
        "records": count,
        "bytes": total,
        "dtype": "uint8",
        "separator": SEPARATOR.decode("utf-8"),
        "packed_sha256": digest.hexdigest(),
        "tokenizer_mode": "byte-smoke-path; production tokenizer pending",
    }
    args.output.with_suffix(args.output.suffix + ".json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
