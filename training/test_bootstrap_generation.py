#!/usr/bin/env python3
"""Generate a few local responses from the Mikoo bootstrap checkpoint."""
from __future__ import annotations

import argparse
import struct

import numpy as np

MAGIC = b"MKGRU01\0"
VOCAB = 256
EMBED = 128
HIDDEN = 256


def load(path: str):
    raw = open(path, "rb").read()
    header = len(MAGIC) + 16
    assert raw[: len(MAGIC)] == MAGIC
    vocab, embed, hidden, _ = struct.unpack("<IIII", raw[len(MAGIC) : header])
    assert (vocab, embed, hidden) == (VOCAB, EMBED, HIDDEN)
    offset = header
    sizes = [
        VOCAB * EMBED,
        3 * HIDDEN * EMBED,
        3 * HIDDEN * HIDDEN,
        3 * HIDDEN,
        3 * HIDDEN,
        VOCAB * HIDDEN,
        VOCAB,
    ]
    arrays = []
    for size in sizes:
        arrays.append(np.frombuffer(raw, dtype="<f4", count=size, offset=offset).reshape(-1).copy())
        offset += size * 4
    return arrays


def generate(arrays, user: str, limit: int = 180) -> str:
    embedding, weight_ih, weight_hh, bias_ih, bias_hh, output_weight, output_bias = arrays
    embedding = embedding.reshape(VOCAB, EMBED)
    weight_ih = weight_ih.reshape(3 * HIDDEN, EMBED)
    weight_hh = weight_hh.reshape(3 * HIDDEN, HIDDEN)
    bias_ih = bias_ih.reshape(3 * HIDDEN)
    bias_hh = bias_hh.reshape(3 * HIDDEN)
    output_weight = output_weight.reshape(VOCAB, HIDDEN)
    output_bias = output_bias.reshape(VOCAB)
    hidden = np.zeros(HIDDEN, dtype=np.float32)

    def step(token: int):
        x = embedding[token]
        input_gate = bias_ih.copy()
        recurrent_gate = bias_hh.copy()
        input_gate += weight_ih @ x
        recurrent_gate += weight_hh @ hidden
        reset = 1.0 / (1.0 + np.exp(-(input_gate[:HIDDEN] + recurrent_gate[:HIDDEN])))
        update = 1.0 / (1.0 + np.exp(-(input_gate[HIDDEN : 2 * HIDDEN] + recurrent_gate[HIDDEN : 2 * HIDDEN])))
        candidate = np.tanh(input_gate[2 * HIDDEN :] + reset * recurrent_gate[2 * HIDDEN :])
        return (1.0 - update) * candidate + update * hidden

    for byte in ("<|user|>\n" + user + "\n<|assistant|>\n").encode("utf-8"):
        hidden = step(byte)
    result = bytearray()
    for _ in range(limit):
        scores = output_weight @ hidden + output_bias
        token = int(np.argmax(scores))
        result.append(token)
        hidden = step(token)
        if b"<|end|>" in result:
            break
    return bytes(result).split(b"<|end|>", 1)[0].decode("utf-8", errors="replace").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("--limit", type=int, default=768)
    args = parser.parse_args()
    arrays = load(args.checkpoint)
    for prompt in (
        "Hello",
        "Fix a bug in my selected file",
        "Write tests for this function",
        "Write a Python function to safely divide two numbers",
        "Write a Kotlin function that returns a non-empty trimmed name",
        "Write a C++17 function to find a value safely",
        "Generate a README for a small coding project",
    ):
        response = generate(arrays, prompt, args.limit)
        print(f"PROMPT: {prompt}\nOUTPUT_UNITS: {len(response.encode('utf-8'))}\nRESPONSE: {response}\n")


if __name__ == "__main__":
    main()
