# Mikoo AI Runtime Research Notes

## Official sources reviewed

1. llama.cpp repository: https://github.com/ggml-org/llama.cpp
2. ExecuTorch XNNPACK backend documentation: https://docs.pytorch.org/executorch/stable/backends/xnnpack/xnnpack-overview.html

## Findings

The official llama.cpp repository describes a plain C/C++ implementation with minimal dependencies, ARM-oriented optimization paths, and integer quantization options ranging from 1.5-bit through 8-bit. The repository is therefore a strong candidate for CPU-only local inference, but the exact Android build, GGUF model support, mmap behavior, and custom tiny-architecture support must be verified against the selected commit and model format before final integration. Repository URL: https://github.com/ggml-org/llama.cpp

The official ExecuTorch XNNPACK documentation states that XNNPACK is intended for CPU execution on mobile CPUs, supports Arm and x86, supports ARM64 on Android, and supports ARMv7 with NEON on Android. It documents support for FP32/FP16 activations and 8-bit quantization, and describes building the XNNPACK backend with `-DEXECUTORCH_BUILD_XNNPACK=ON` and linking the `executorch_backends` target. This makes ExecuTorch/XNNPACK a credible INT8 comparison path, but not an obvious pure-INT4 release path from the cited page. Source: https://docs.pytorch.org/executorch/stable/backends/xnnpack/xnnpack-overview.html

## Planning implication

The current runtime shortlist should prefer a GGUF-compatible C/C++ runtime for INT4 experimentation and retain ExecuTorch/XNNPACK as an ARM/Android INT8 comparison. Runtime choice remains provisional until a tiny decoder-only model is converted and measured on Android.

## Additional official sources reviewed

3. ONNX Runtime mobile deployment: https://onnxruntime.ai/docs/tutorials/mobile/
4. Google LiteRT overview: https://developers.google.com/edge/litert

## Additional findings

ONNX Runtime's mobile guidance states that the model must be in ONNX format and must fit both device disk and memory. It recommends starting with the CPU Execution Provider for quantized models and XNNPACK for non-quantized models, while noting that accelerator performance is device- and model-specific and may degrade when unsupported operators cause partitioning. Source: https://onnxruntime.ai/docs/tutorials/mobile/

Google's current LiteRT overview positions LiteRT as an on-device framework built on TensorFlow Lite, with conversion and post-training quantization workflows, Android Interpreter/CompiledModel APIs, and a generative-AI path through LiteRT-LM. The cited overview is strong evidence that LiteRT is viable for Android deployment and quantization, but it does not by itself establish a lightweight pure-INT4 decoder-only text-generation path for Mikoo; that must be tested with the selected architecture. Source: https://developers.google.com/edge/litert

## Planning implication

The runtime decision matrix should treat llama.cpp/GGUF as the primary INT4 candidate, ExecuTorch/XNNPACK as the primary ARM/Android INT8 comparison, and ONNX Runtime Mobile/LiteRT as secondary baselines whose package size, operator coverage, KV-cache handling, and autoregressive generation overhead must be measured before adoption.

## Research sources for tokenizer and training

5. SentencePiece paper: https://aclanthology.org/D18-2012.pdf
6. Hoffmann et al., compute-optimal language-model training: https://proceedings.neurips.cc/paper_files/paper/2022/hash/c1e2faff6f588870935f114ebe04a3e5-Abstract-Conference.html

## Findings

The SentencePiece paper describes a language-independent subword tokenizer and detokenizer that can train directly from raw sentences, and reports implementations of BPE and unigram segmentation. This supports selecting a compact raw-text subword tokenizer for mixed English, Bengali, and Hindi data, while still requiring direct evaluation of token fertility and vocabulary allocation for the target scripts. Source: https://aclanthology.org/D18-2012.pdf

The NeurIPS compute-optimal training study reports that, within its tested regime, model size and training-token count should scale approximately together under a fixed compute budget. This is a useful planning heuristic, not a guarantee outside its tested regime. For Mikoo, it supports avoiding a large undertrained student and allocating a deliberate token budget to the selected small model, followed by task-focused instruction tuning and distillation. Source: https://proceedings.neurips.cc/paper_files/paper/2022/hash/c1e2faff6f588870935f114ebe04a3e5-Abstract-Conference.html
