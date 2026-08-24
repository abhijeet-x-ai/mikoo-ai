#!/usr/bin/env python3
"""Conservative JSONL cleaner for Mikoo text and instruction data.

Expected input records contain `text` or `messages`. The script intentionally
leaves content policy decisions explicit and writes a source manifest so data
provenance is reviewable before training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import unicodedata
from pathlib import Path

CONTROL_RE = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = CONTROL_RE.sub(" ", text)
    text = URL_RE.sub(" <URL> ", text)
    return WS_RE.sub(" ", text).strip()


def extract_text(record: dict) -> str:
    if isinstance(record.get("text"), str):
        return record["text"]
    messages = record.get("messages")
    if isinstance(messages, list):
        parts = []
        for message in messages:
            if isinstance(message, dict) and isinstance(message.get("content"), str):
                role = str(message.get("role", "user"))
                parts.append(f"<{role}> {message['content']}")
        return "\n".join(parts)
    return ""


def record_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                yield line_number, value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-chars", type=int, default=16)
    parser.add_argument("--max-chars", type=int, default=20000)
    parser.add_argument("--language", choices=["en", "bn", "hi", "mixed"], default="mixed")
    parser.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    accepted: list[dict] = []
    rejected = {"invalid": 0, "empty_or_length": 0, "duplicate": 0}

    for line_number, raw in read_jsonl(args.input):
        text = normalize(extract_text(raw))
        if len(text) < args.min_chars or len(text) > args.max_chars:
            rejected["empty_or_length"] += 1
            continue
        digest = record_hash(text)
        if digest in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(digest)
        accepted.append({
            "text": text,
            "language": raw.get("language", args.language),
            "source": raw.get("source", str(args.input)),
            "source_line": line_number,
            "content_sha256": digest,
        })

    random.Random(args.seed).shuffle(accepted)
    n = len(accepted)
    train_end = int(n * 0.98)
    valid_end = train_end + int(n * 0.01)
    splits = {
        "train": accepted[:train_end],
        "validation": accepted[train_end:valid_end],
        "test": accepted[valid_end:],
    }
    for name, records in splits.items():
        with (args.output_dir / f"{name}.jsonl").open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "normalization": "NFKC + control removal + URL placeholder + whitespace collapse",
        "language_label_default": args.language,
        "seed": args.seed,
        "accepted": n,
        "split_counts": {name: len(records) for name, records in splits.items()},
        "rejected": rejected,
        "pii_and_toxicity_filter": "REQUIRED REVIEW STEP: not implemented by this stdlib utility",
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
