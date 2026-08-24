#!/usr/bin/env python3
"""Validate the binary contract shared by the bootstrap trainer and JNI loader."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np

MAGIC = b"MKGRU01\0"
VOCAB = 256
EMBED = 128
HIDDEN = 256
FLOATS = (
    VOCAB * EMBED
    + 3 * HIDDEN * EMBED
    + 3 * HIDDEN * HIDDEN
    + 3 * HIDDEN
    + 3 * HIDDEN
    + VOCAB * HIDDEN
    + VOCAB
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    raw = args.checkpoint.read_bytes()
    header_size = len(MAGIC) + 16
    if raw[: len(MAGIC)] != MAGIC:
        raise SystemExit("invalid bootstrap checkpoint magic")
    dims = struct.unpack("<IIII", raw[len(MAGIC) : header_size])
    if dims[:3] != (VOCAB, EMBED, HIDDEN):
        raise SystemExit(f"invalid dimensions: {dims}")
    expected_size = header_size + FLOATS * 4
    if len(raw) != expected_size:
        raise SystemExit(f"invalid size: {len(raw)} != {expected_size}")
    values = np.frombuffer(raw, dtype="<f4", offset=header_size)
    if not np.isfinite(values).all():
        raise SystemExit("checkpoint contains non-finite weights")
    print(f"bootstrap checkpoint valid: bytes={len(raw)} floats={len(values)}")


if __name__ == "__main__":
    main()
