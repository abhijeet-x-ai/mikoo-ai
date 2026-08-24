#!/usr/bin/env python3
"""Minimal causal-LM trainer for Mikoo's frozen architecture.

Input is a NumPy int64 token array produced by the tokenizer pipeline. This
script is intentionally conservative: it refuses to silently run without
PyTorch and writes checkpoints with the architecture metadata.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

try:
    import numpy as np
    import torch
    import torch.nn as nn
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("Install numpy and torch on the training machine before running train.py") from exc

VOCAB = 24_576
LAYERS = 24
HIDDEN = 1_152
QUERY_HEADS = 18
KV_HEADS = 2
HEAD_DIM = 64
INTERMEDIATE = 3_072


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.weight * (x * x).mean(-1, keepdim=True).add(self.eps).rsqrt() * x


class SwiGLU(nn.Module):
    def __init__(self):
        super().__init__()
        self.w_gate = nn.Linear(HIDDEN, INTERMEDIATE, bias=False)
        self.w_up = nn.Linear(HIDDEN, INTERMEDIATE, bias=False)
        self.w_down = nn.Linear(INTERMEDIATE, HIDDEN, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w_down(torch.nn.functional.silu(self.w_gate(x)) * self.w_up(x))


class MQA(nn.Module):
    def __init__(self):
        super().__init__()
        self.q = nn.Linear(HIDDEN, QUERY_HEADS * HEAD_DIM, bias=False)
        self.k = nn.Linear(HIDDEN, KV_HEADS * HEAD_DIM, bias=False)
        self.v = nn.Linear(HIDDEN, KV_HEADS * HEAD_DIM, bias=False)
        self.o = nn.Linear(QUERY_HEADS * HEAD_DIM, HIDDEN, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, seq, _ = x.shape
        q = self.q(x).view(batch, seq, QUERY_HEADS, HEAD_DIM).transpose(1, 2)
        k = self.k(x).view(batch, seq, KV_HEADS, HEAD_DIM).transpose(1, 2)
        v = self.v(x).view(batch, seq, KV_HEADS, HEAD_DIM).transpose(1, 2)
        k = k.expand(-1, QUERY_HEADS, -1, -1)
        v = v.expand(-1, QUERY_HEADS, -1, -1)
        causal = torch.ones(seq, seq, device=x.device, dtype=torch.bool).tril()
        y = torch.nn.functional.scaled_dot_product_attention(q, k, v, attn_mask=causal)
        return self.o(y.transpose(1, 2).contiguous().view(batch, seq, QUERY_HEADS * HEAD_DIM))


class Block(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm1 = RMSNorm(HIDDEN)
        self.attn = MQA()
        self.norm2 = RMSNorm(HIDDEN)
        self.mlp = SwiGLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        return x + self.mlp(self.norm2(x))


class MikooModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB, HIDDEN)
        self.blocks = nn.ModuleList(Block() for _ in range(LAYERS))
        self.final_norm = RMSNorm(HIDDEN)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        x = self.embedding(tokens)
        for block in self.blocks:
            x = block(x)
        x = self.final_norm(x)
        # Weight tying: output projection reuses the embedding matrix.
        return x @ self.embedding.weight.t()


def batches(tokens: np.ndarray, context: int, batch_size: int, device: torch.device):
    if tokens.ndim != 1 or tokens.dtype.kind not in "iu":
        raise ValueError("tokens must be a one-dimensional integer NumPy array")
    if len(tokens) <= context + 1:
        raise ValueError("token array is shorter than context + 1")
    while True:
        starts = np.random.randint(0, len(tokens) - context - 1, size=batch_size)
        x = np.stack([tokens[i:i + context] for i in starts])
        y = np.stack([tokens[i + 1:i + context + 1] for i in starts])
        yield torch.from_numpy(x).long().to(device), torch.from_numpy(y).long().to(device)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokens", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--context", type=int, choices=[256, 512, 1024, 2048], default=512)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accumulation", type=int, default=32)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--allow-cpu-production", action="store_true", help="allow the 354M model on CPU; unsafe for the default sandbox")
    args = parser.parse_args()

    device = torch.device(args.device)
    if device.type == "cpu" and not args.allow_cpu_production:
        raise SystemExit(
            "The 354M production trainer requires a CUDA-capable training machine. "
            "Use train_bootstrap_gru.py for local smoke tests, or pass --allow-cpu-production "
            "only after provisioning enough host memory."
        )
    tokens = np.load(args.tokens, mmap_mode="r")
    model = MikooModel().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1)
    iterator = batches(tokens, args.context, args.batch_size, device)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    model.train()
    started = time.time()
    optimizer.zero_grad(set_to_none=True)
    for step in range(1, args.steps + 1):
        x, y = next(iterator)
        logits = model(x)
        loss = torch.nn.functional.cross_entropy(logits.reshape(-1, VOCAB), y.reshape(-1))
        (loss / args.grad_accumulation).backward()
        if step % args.grad_accumulation == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        if step == 1 or step % 100 == 0:
            print(f"step={step} loss={loss.item():.5f} elapsed_s={time.time() - started:.1f}")
        if step % 1000 == 0 or step == args.steps:
            torch.save({
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "step": step,
                "model_spec": {
                    "vocab_size": VOCAB, "layers": LAYERS, "hidden": HIDDEN,
                    "query_heads": QUERY_HEADS, "kv_heads": KV_HEADS,
                    "head_dim": HEAD_DIM, "intermediate": INTERMEDIATE,
                    "context": args.context,
                },
            }, args.out)


if __name__ == "__main__":
    main()
