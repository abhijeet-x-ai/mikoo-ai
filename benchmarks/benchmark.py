#!/usr/bin/env python3
"""Mikoo benchmark report generator.

This script records measured values supplied by a host/device runner. It does
not invent tokens/sec, RAM, battery, or thermal values. Use `--sample` to
create a clearly labeled template row, or provide JSON records with `--input`.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

FIELDS = [
    "device", "android_version", "abi", "runtime", "model_file_mb",
    "apk_mb", "context_tokens", "generation_tokens", "load_ms",
    "first_token_ms", "tokens_per_sec", "peak_rss_mb", "avg_rss_mb",
    "native_heap_mb", "managed_heap_mb", "cpu_percent", "battery_pct",
    "temperature_c", "cancel_ok", "crash_or_anr", "offline_ok", "notes",
]


def read_records(path: Path) -> list[dict]:
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an object or list of objects")
    return payload


def validate(records: list[dict]) -> None:
    required = {"device", "context_tokens", "offline_ok", "crash_or_anr"}
    for index, record in enumerate(records):
        missing = required - record.keys()
        if missing:
            raise ValueError(f"record {index} missing required fields: {sorted(missing)}")
        if int(record["context_tokens"]) not in {256, 512, 1024, 2048}:
            raise ValueError("context_tokens must be one of 256, 512, 1024, 2048")


def write_csv(records: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_markdown(records: list[dict], output: Path) -> None:
    lines = [
        "# Mikoo AI benchmark report",
        "",
        "Values in this report are measurements only when supplied by a host/device runner. Blank fields are unknown; estimates must be explicitly labeled in notes.",
        "",
        "| Device | ABI | Runtime | Context | Load ms | First token ms | Tokens/sec | Peak RSS MB | Offline | Crash/ANR |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in records:
        lines.append(
            f"| {r.get('device', '')} | {r.get('abi', '')} | {r.get('runtime', '')} | "
            f"{r.get('context_tokens', '')} | {r.get('load_ms', '')} | {r.get('first_token_ms', '')} | "
            f"{r.get('tokens_per_sec', '')} | {r.get('peak_rss_mb', '')} | {r.get('offline_ok', '')} | "
            f"{r.get('crash_or_anr', '')} |"
        )
    lines += ["", "## Notes", ""]
    for r in records:
        if r.get("notes"):
            lines.append(f"- {r.get('device', 'unknown device')}: {r['notes']}")
    output.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    if args.sample:
        records = [{
            "device": "UNMEASURED_TEMPLATE",
            "android_version": "",
            "abi": "arm64-v8a",
            "runtime": "pending",
            "model_file_mb": "",
            "apk_mb": "",
            "context_tokens": 512,
            "generation_tokens": "",
            "load_ms": "",
            "first_token_ms": "",
            "tokens_per_sec": "",
            "peak_rss_mb": "",
            "avg_rss_mb": "",
            "native_heap_mb": "",
            "managed_heap_mb": "",
            "cpu_percent": "",
            "battery_pct": "",
            "temperature_c": "",
            "cancel_ok": "",
            "crash_or_anr": "",
            "offline_ok": "",
            "notes": "Template only; no device measurement has been performed.",
        }]
    elif args.input:
        records = read_records(args.input)
    else:
        parser.error("use --sample or --input records.json")
    validate(records)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(records, args.output_dir / "mikoo-benchmark.csv")
    write_markdown(records, args.output_dir / "mikoo-benchmark.md")
    print(f"wrote {len(records)} records to {args.output_dir}")


if __name__ == "__main__":
    main()
