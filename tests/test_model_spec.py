#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

SPEC = json.loads((Path(__file__).parents[1] / "model" / "model_spec.json").read_text())


def test_exact_parameter_count() -> None:
    assert SPEC["parameter_count_exact"] == 353_950_848
    formula = SPEC["parameter_count_formula"]
    assert formula["tied_embedding"] == 24_576 * 1_152
    assert formula["attention_per_layer"] == 1_152 * 1_152 + 1_152 * 1_152 + 1_152 * 128 + 1_152 * 128
    assert formula["swiglu_per_layer"] == 3 * 1_152 * 3_072
    assert formula["transformer_block_per_layer"] == 13_568_256
    assert formula["transformer_blocks"] == 24 * 13_568_256


def test_mobile_contract() -> None:
    assert SPEC["default_context_tokens"] == 512
    assert SPEC["recommended_context_tokens"] == 1024
    assert SPEC["maximum_context_tokens"] == 2048
    assert SPEC["num_kv_heads"] == 2
    assert SPEC["ram_policy"]["hard_peak_application_mb"] == 749
    assert SPEC["ram_policy"]["preferred_peak_application_mb"] == 650
    assert SPEC["ram_policy"]["default_context_tokens"] == 512
    assert SPEC["ram_policy"]["recommended_context_tokens"] == 1024
    assert SPEC["ram_policy"]["stress_context_tokens"] == 2048
    assert SPEC["storage_policy"]["conversation_history_is_disk_backed"] is True
    assert SPEC["storage_policy"]["disk_cache_is_bounded_by_user_setting"] is True
    assert SPEC["tie_input_output_embeddings"] is True
    assert SPEC["requires_network_at_inference"] is False


if __name__ == "__main__":
    test_exact_parameter_count()
    test_mobile_contract()
    print("model specification checks passed")
