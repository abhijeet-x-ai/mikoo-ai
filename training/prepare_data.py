#!/usr/bin/env python3
"""License-aware JSONL cleaner for Mikoo text and code training data.

The utility is intentionally conservative. It never downloads data, calls an
AI service, or treats a dataset-level license as permission for every record.
High-data runs should use --require-license and --preserve-code.
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
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
)
LICENSE_ALLOWLIST = {
    "0BSD", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "CC-BY-4.0",
    "CC0-1.0", "ISC", "MIT", "UNLICENSE", "PUBLIC-DOMAIN",
}
LICENSE_FIELDS = ("license", "license_id", "license_spdx", "spdx_license")


def normalize(text: str, preserve_code: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = CONTROL_RE.sub(" ", text)
    if preserve_code:
        lines = [line.rstrip() for line in text.split("\n")]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        result = "\n".join(lines)
        return re.sub(r"\n{4,}", "\n\n\n", result)
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
                parts.append(f"<{role}>\n{message['content']}")
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
                yield line_number, None
                continue
            yield line_number, value if isinstance(value, dict) else None


def license_id(record: dict) -> str:
    for field in LICENSE_FIELDS:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return ""


def license_allowed(record: dict) -> bool:
    value = license_id(record)
    return value in LICENSE_ALLOWLIST


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-chars", type=int, default=16)
    parser.add_argument("--max-chars", type=int, default=20000)
    parser.add_argument("--language", choices=["en", "bn", "hi", "mixed"], default="mixed")
    parser.add_argument("--seed", type=int, default=20260824)
    parser.add_argument("--require-license", action="store_true")
    parser.add_argument("--preserve-code", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    accepted: list[dict] = []
    rejected = {"invalid": 0, "empty_or_length": 0, "duplicate": 0, "license": 0, "secret": 0}

    for line_number, raw in read_jsonl(args.input):
        if raw is None:
            rejected["invalid"] += 1
            continue
        if args.require_license and not license_allowed(raw):
            rejected["license"] += 1
            continue
        text = normalize(extract_text(raw), preserve_code=args.preserve_code)
        if len(text) < args.min_chars or len(text) > args.max_chars:
            rejected["empty_or_length"] += 1
            continue
        if contains_secret(text):
            rejected["secret"] += 1
            continue
        digest = record_hash(text)
        if digest in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(digest)
        accepted.append({
            "text": text,
            "language": raw.get("language", args.language),
            "task_type": raw.get("task_type", "pretraining"),
            "source": raw.get("source", str(args.input)),
            "source_url": raw.get("source_url", ""),
            "repository": raw.get("repository", ""),
            "path": raw.get("path", ""),
            "license": license_id(raw),
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
        "normalization": "NFKC + control removal + optional code-format preservation",
        "license_allowlist": sorted(LICENSE_ALLOWLIST),
        "require_license": args.require_license,
        "language_label_default": args.language,
        "seed": args.seed,
        "accepted": n,
        "split_counts": {name: len(records) for name, records in splits.items()},
        "rejected": rejected,
        "near_duplicate_filter": "repository/function-level filter required before production training",
        "toxicity_pii_review": "required review step outside this stdlib utility",
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
