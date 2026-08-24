#!/usr/bin/env python3
"""Train a tiny self-authored byte-level Mikoo bootstrap model.

This is a real local neural checkpoint for smoke testing the Android inference
path. It is not the planned 354M-parameter production model. The corpus must be
license-safe and local; this script never downloads data or calls an AI service.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
import torch
from torch import nn

MAGIC = b"MKGRU01\0"
VOCAB = 256
EMBED = 128
HIDDEN = 256
SEQ_LEN = 192


class BootstrapGRU(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding = nn.Embedding(VOCAB, EMBED)
        self.rnn = nn.GRU(EMBED, HIDDEN, batch_first=True)
        self.output = nn.Linear(HIDDEN, VOCAB)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        hidden, _ = self.rnn(self.embedding(tokens))
        return self.output(hidden)


def export_checkpoint(model: BootstrapGRU, output: Path) -> None:
    state = model.state_dict()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        handle.write(MAGIC)
        handle.write(struct.pack("<IIII", VOCAB, EMBED, HIDDEN, 0))
        for key in (
            "embedding.weight",
            "rnn.weight_ih_l0",
            "rnn.weight_hh_l0",
            "rnn.bias_ih_l0",
            "rnn.bias_hh_l0",
            "output.weight",
            "output.bias",
        ):
            array = state[key].detach().cpu().contiguous().numpy().astype("<f4")
            handle.write(array.tobytes(order="C"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=2400)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260824)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    torch.set_num_threads(min(4, torch.get_num_threads()))
    raw = args.corpus.read_bytes()
    if len(raw) < SEQ_LEN + 2:
        raise SystemExit("bootstrap corpus is too short")
    tokens = torch.from_numpy(np.frombuffer(raw, dtype=np.uint8).copy()).long()
    model = BootstrapGRU()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=0.0)
    model.train()
    for step in range(1, args.steps + 1):
        starts = torch.randint(0, len(tokens) - SEQ_LEN - 1, (args.batch_size,))
        batch = torch.stack([tokens[start : start + SEQ_LEN] for start in starts])
        target = torch.stack([tokens[start + 1 : start + SEQ_LEN + 1] for start in starts])
        logits = model(batch)
        loss = nn.functional.cross_entropy(logits.reshape(-1, VOCAB), target.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step == 1 or step % 200 == 0:
            print(f"step={step} loss={loss.item():.5f}")
    export_checkpoint(model, args.out)
    print(f"wrote {args.out} bytes={args.out.stat().st_size}")


if __name__ == "__main__":
    main()
