#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]

def main() -> None:
    text = (ROOT / "training/config.yaml").read_text()
    required_fragments = [
        "project: mikoo-medium-coding-multilingual-v0.3",
        "candidates: [16384, 24576, 32768]",
        "teacher_used_during_inference: false",
        "mobile_peak_memory_mb_ceiling: 749",
        "train: 0.98",
        "validation: 0.01",
        "test: 0.01",
        "default_context_tokens: 512",
        "stress_context_tokens: 2048",
    ]
    for fragment in required_fragments:
        assert fragment in text, fragment
    assert "\n distillation:" not in text
    print("training configuration structural validation passed")


if __name__ == "__main__":
    main()
