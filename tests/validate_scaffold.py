#!/usr/bin/env python3
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).parents[1]
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


def main() -> None:
    spec = json.loads((ROOT / "model/model_spec.json").read_text())
    tool_schema = json.loads((ROOT / "model/coding_agent_tools.schema.json").read_text())
    code_schema = json.loads((ROOT / "training/code_record.schema.json").read_text())
    assert tool_schema["title"] == "Mikoo Coding Agent Action"
    assert code_schema["title"] == "Mikoo Coding Training Record"
    assert "license" in code_schema["required"]
    assert "split" in code_schema["required"]
    assert "apply_patch" in tool_schema["properties"]["action"]["enum"]
    assert spec["require_user_approval_for_writes"] is True
    assert spec["require_user_approval_for_execution"] is True
    assert spec["parameter_count_exact"] == 353_950_848
    assert spec["vocab_size"] == 24_576
    assert spec["default_context_tokens"] == 512
    assert spec["maximum_context_tokens"] == 2048

    layout_text = (ROOT / "android/app/src/main/res/layout/activity_main.xml").read_text()
    assert "@+id/open_workspace_button" in layout_text
    assert "@+id/workspace_status" in layout_text

    manifest = ET.parse(ROOT / "android/app/src/main/AndroidManifest.xml").getroot()
    permissions = [node.attrib.get(ANDROID_NS + "name", "") for node in manifest.findall("uses-permission")]
    forbidden = {"android.permission.INTERNET", "android.permission.RECORD_AUDIO", "android.permission.READ_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE"}
    assert not forbidden.intersection(permissions), permissions

    required = [
        ROOT / "README.md",
        ROOT / "training/prepare_data.py",
        ROOT / "benchmarks/benchmark.py",
        ROOT / "android/app/src/main/cpp/mikoo_jni.cpp",
        ROOT / "android/app/src/main/java/com/mikoo/ai/MainActivity.kt",
    ]
    for path in required:
        assert path.exists(), path
    print("Mikoo scaffold validation passed")


if __name__ == "__main__":
    main()
