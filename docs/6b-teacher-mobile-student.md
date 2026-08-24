# Mikoo 6B teacher and mobile student profile

## Decision

A dense 6B-parameter model cannot be packaged as a 749 MB Android application model. Raw weight storage is approximately 12.00 GB at FP16, 6.00 GB at INT8, 3.00 GB at INT4, 2.25 GB at INT3, and 1.50 GB at INT2 before tensor metadata, runtime workspaces, tokenizer, allocator fragmentation, and KV cache. Therefore a 6B model is a **training-time teacher or high-memory desktop profile**, not the direct 2 GB-phone runtime.

The 2 GB-phone target should use a distilled Mikoo student. The current 354M design is the safe baseline. A future 500–700M INT4 student can be evaluated against the 749 MB cap, but it must be measured on real devices before release. A 1B INT4 model has approximately 500 MB of raw weights before runtime overhead and is too close to the cap for the default low-memory profile.

## Recommended profiles

| Profile | Parameters | Raw INT4 weights | Runtime role | 2 GB phone |
|---|---:|---:|---|---|
| Mikoo Nano | 395K bootstrap | 0.2 MB equivalent | Current integration smoke model | Yes |
| Mikoo Mobile | 354M | ~169 MiB | Current planned mobile baseline | Candidate; measure PSS |
| Mikoo Mobile Plus | 500–700M | ~238–334 MiB | Distilled production candidate | Candidate; strict device testing required |
| Mikoo Teacher | 6B | ~2.79 GiB raw | High-memory training/distillation only | No |

## Distillation workflow

The 6B teacher is used only on an authorized training machine. It produces bounded plans, code completions, explanations, tests, patch proposals, tool-action examples, and failure/refinement trajectories. Each sample is filtered for license/provenance compliance, syntax or test validity where executable validation is available, safety, output length, and schema validity. The student learns from the filtered targets; the teacher and its weights are never packaged in the APK and are never required at inference time.

The mobile student should use a 512-token default context, batch size one, one worker, INT4-group weights, bounded KV cache, and a 768-token default output ceiling with a lower-memory degradation path. Context and output limits must be independently configurable because long output increases latency and temporary memory even when weights are unchanged.

## Important qualification

Quantization reduces storage and working memory but does not make a 6B model fit inside 749 MB. The official llama.cpp quantization documentation shows that quantized model size remains proportional to parameter count and that quantization may introduce accuracy loss [1]. On-device evaluation research reports that memory and performance depend on effective bits-per-weight, quantization method, and hardware [2]. Mobile GPU research demonstrates that optimized kernels can improve throughput, but it does not remove the weight-memory boundary [3].

## References

[1]: https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md "llama.cpp quantization documentation"
[2]: https://arxiv.org/abs/2505.15030 "A Systematic Evaluation of On-Device LLMs: Quantization, Performance, and Resources"
[3]: https://arxiv.org/abs/2403.20041 "Transformer-Lite: High-efficiency Deployment of Large Language Models on Mobile Phone GPUs"
