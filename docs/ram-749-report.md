# Mikoo AI — 749 MB RAM and expandable-storage optimization report

**Requirement clarified:** Storage is not a hard 5 GB ceiling. The model, multiple model variants, conversation history, and disk caches may use more storage when the user allows it. The hard runtime requirement is that the **Mikoo application process must remain at or below 749 MB peak RAM**, while the default profile should remain comfortable on a 2 GB RAM Android phone.

## Decision

The revised primary model target is a **353,950,848-parameter** decoder-only Transformer. It uses a 24,576-token English/Bengali/Hindi vocabulary, 24 layers, hidden size 1,152, 18 query heads, two KV heads, 64-dimensional heads, 3,072-unit SwiGLU, RMSNorm, RoPE, tied embeddings, and no projection bias.

The preferred release format is **INT4 group quantization**. Theoretical model weights are approximately **199.1 MB including the planning metadata allowance**. The conservative application envelope is estimated at **525.4 MB with 512-token context**, **531.7 MB with 1,024-token context**, and **544.3 MB with 2,048-token stress context**. These values are planning estimates, not Android measurements. They leave an estimated 205–224 MB below the 749 MB hard cap for device variation, but the actual PSS/RSS must be measured on the target phones.

The default 2 GB-device profile should use INT4-group weights, 512-token context, one inference worker, batch size one, bounded conversation history, and a generation cap of 256 tokens. A 1,024-token context profile can be enabled after device validation. A 2,048-token profile is a stress mode, not the default.

## Exact architecture

| Component | Value |
|---|---:|
| Parameters | 353,950,848 exactly |
| Vocabulary | 24,576 |
| Layers | 24 |
| Hidden size | 1,152 |
| Query heads | 18 |
| KV heads | 2 |
| Head dimension | 64 |
| Feed-forward | SwiGLU, intermediate size 3,072 |
| Normalization | RMSNorm |
| Positional encoding | RoPE |
| Embeddings | Input/output tied |
| Biases | Disabled |
| Default context | 512 tokens |
| Recommended context | 1,024 tokens |
| Stress context | 2,048 tokens |
| Inference batch | 1 |
| Primary quantization | INT4 group |

Parameter calculation:

- Tied embedding: \(24,576 \times 1,152 = 28,311,552\).
- Attention per layer: \(1,152^2 + 1,152^2 + 1,152\times128 + 1,152\times128 = 2,949,120\).
- SwiGLU per layer: \(3 \times 1,152 \times 3,072 = 10,616,832\).
- RMSNorm vectors per layer: \(2 \times 1,152 = 2,304\).
- Transformer block per layer: \(2,949,120 + 10,616,832 + 2,304 = 13,568,256\).
- Twenty-four blocks: \(24 \times 13,568,256 = 325,638,144\).
- Final RMSNorm: 1,152.
- **Total: 28,311,552 + 325,638,144 + 1,152 = 353,950,848 parameters.**

## Weight-size calculations

| Format | Theoretical weight size |
|---|---:|
| FP32 | 1,415.8 MB |
| FP16 | 707.9 MB |
| INT8 | 354.0 MB |
| Ideal INT4 | 177.0 MB |
| INT4-group estimate | 199.1 MB including a small metadata allowance |
| Mixed precision estimate | 309.7 MB |

The INT4-group candidate is the only practical default for this target. FP16 nearly consumes the entire 749 MB budget before runtime memory, and INT8 leaves less room for workspaces, UI, and memory pressure. The actual converted model file must be measured because headers, alignment, scales, tensor metadata, tokenizer data, and packaging can change the result.

## KV-cache budget

For batch size one, FP16 K/V cache is calculated as:

\[
2 \times L \times B \times H_{KV} \times T \times d_{head} \times 2
\]

where the first factor of two represents K and V, and the final factor of two is FP16 bytes.

| Context | FP16 KV cache | INT8 KV cache |
|---:|---:|---:|
| 256 tokens | 1.573 MB | 0.786 MB |
| 512 tokens | 3.146 MB | 1.573 MB |
| 1,024 tokens | 6.291 MB | 3.146 MB |
| 2,048 tokens | 12.583 MB | 6.291 MB |

KV cache is not the dominant memory cost in this architecture; weights, runtime workspace, allocator behavior, thread stacks, and page residency are more important. Nevertheless, context must remain bounded for latency and battery reasons.

## Conservative application envelope

The following is an engineering estimate that deliberately reserves 150 MB of safety headroom. It is not a measured device result.

| Component | Planning value |
|---|---:|
| INT4-group model and metadata | 201.1 MB |
| Tokenizer runtime | 8.0 MB |
| Activations and scratch/workspace | 80.0 MB |
| Native runtime and allocator | 40.0 MB |
| Kotlin/Java heap and minimal UI | 40.0 MB |
| FP16 KV cache at 512 tokens | 3.1 MB |
| Safety headroom | 150.0 MB |
| **Estimated peak at 512 tokens** | **525.4 MB** |
| FP16 KV cache at 1,024 tokens | 6.3 MB |
| **Estimated peak at 1,024 tokens** | **531.7 MB** |
| FP16 KV cache at 2,048 tokens | 12.6 MB |
| **Estimated peak at 2,048 tokens** | **544.3 MB** |

The hard process cap is **749 MB**, but the operational target is **650 MB or less**. The extra space is not a license to allocate freely: Android may kill or throttle an application under system-wide pressure even when the process is below its own cap.

## 2 GB phone operating profiles

| Profile | Quantization | Context | Generation cap | Intended use |
|---|---|---:|---:|---|
| Smooth default | INT4-group | 512 | 256 tokens | Default for 2 GB devices; one worker, batch one |
| Balanced | INT4-group | 1,024 | 384 tokens | Enable after real-device memory and thermal tests |
| Long-context stress | INT4-group | 2,048 | 512 tokens | Benchmark/developer mode only |
| Quality fallback | INT8 | 512 | 256 tokens | Use only if quality gain justifies larger memory and slower execution |

“Smoothly” cannot be guaranteed from RAM calculations alone. Token speed depends on CPU cores, ARM microarchitecture, clock throttling, Android version, runtime kernels, thermal state, and background load. The release report must measure first-token latency, tokens/sec, peak PSS/RSS, CPU, battery, temperature, and crashes on an actual low-end 2 GB device.

## Storage policy

Storage does not directly become RAM. The static model can remain around 200 MB in INT4-group format, while the user may store multiple model variants, tokenizer backups, conversation history, exported chats, logs, and optional local knowledge packs. Disk-backed history should be append-only with compaction and a user-configurable quota. The app must expose cache cleanup and must never map all stored models at once.

Recommended storage behavior:

1. Keep only one active model mapped into the process.
2. Store inactive model variants on disk and load them on demand.
3. Store conversation history as compressed, structured records rather than repeatedly duplicating full prompts.
4. Keep diagnostic logs disabled by default or rotate them by size.
5. Maintain a free-space check before downloading or importing a new model.
6. Treat the 5 GB value as an initial package/storage planning point, not a runtime RAM constraint.

## Runtime and optimization strategy

The primary runtime experiment remains a C/C++ GGUF-compatible path with mmap, INT4 group quantization, native KV-cache management, and streaming token generation. ExecuTorch/XNNPACK remains the INT8 comparison. The Android process must use one inference worker by default, fixed or bounded scratch buffers, allocator reuse, prompt truncation by token count, cancellation, and a memory-pressure monitor.

The runtime must enforce a hard application policy: refuse a new generation if measured memory is too close to 749 MB, reduce context, clear/rebuild the cache, release temporary buffers, shorten the generation cap, and stop with a clear status if the process remains above the safety threshold. The app must never intentionally consume all available device RAM.

## Training impact

The larger model is more capable than the previous 72M design but also costs more to train. A rough causal-LM compute estimate of \(6ND\) gives approximately 2.12×10¹⁷ FLOPs for 100M tokens, 1.06×10¹⁸ FLOPs for 500M tokens, and 3.06×10¹⁸ FLOPs for 1.44B tokens. These are planning calculations, not time or price promises. Training requires a suitable GPU environment; the Android phone is an inference target only.

Training should still use the staged tokenizer → pretraining → instruction tuning → distillation → quantization workflow. A smaller smooth-mode student should remain available if the larger model fails measured token-speed or thermal gates on the actual 2 GB device.

## Go/no-go criteria

The revised design passes the **calculated** feasibility gate because the preferred INT4-group estimate remains below 650 MB, below the 749 MB hard cap, and leaves room for runtime variation. It passes the **release** gate only after a real 2 GB Android phone confirms that the default profile is stable, responsive, thermally acceptable, and free of frequent crashes or ANRs. No real token/sec or battery number is claimed in this report.
