# Mikoo AI

Mikoo AI is an offline-first Android **coding agent** designed for low-end ARM phones with a hard application-RAM ceiling of 749 MB, while targeting smooth default inference on 2 GB RAM devices. It focuses on code generation, explanation, unit-test creation, debugging, refactoring, patch proposal, and bounded repository context. The project uses a multilingual decoder-only Transformer, compact subword tokenization, quantized native inference, and a minimal Kotlin chat UI.

## Current status

The revised coding-agent specification uses a planned 353,950,848-parameter model, 24,576 vocabulary tokens, 24 layers, hidden size 1,152, 18 query heads, two KV heads, SwiGLU intermediate size 3,072, tied embeddings, RoPE, RMSNorm, and a 512-token default context. Code-specialization data and structured tool actions are defined under `docs/` and `model/`. It is a calculated design target, not yet a trained checkpoint. The model checkpoint, tokenizer artifact, Android SDK build, and physical-device measurements are not included yet; they are produced by the subsequent training and device-validation stages. Storage is treated as expandable; persistent chat data and caches must still use user-configurable disk quotas to avoid unbounded growth.

Calculated values and estimates are documented in `docs/ram-749-report.md` and `docs/feasibility-output/`. They must not be represented as measured device performance.

## Repository layout

```text
android/       Native Android Gradle project, Kotlin UI, JNI, and C++ bridge
model/         Versioned architecture specification and model manifests
tokenizer/     Tokenizer training notes, tests, and exported artifacts
training/      Dataset preparation, pretraining, SFT, and distillation configs
quantization/  Conversion, quantization, validation, and checksums
benchmarks/    Host/device benchmark harness and report generation
scripts/       Reproducible environment and build helpers
tests/         Unit, integration, memory, and regression tests
docs/          Architecture, model card, data card, and release notes
```

## Offline contract

The release application must work with airplane mode enabled and must not require a backend, API key, telemetry service, INTERNET permission, storage permission, or microphone permission. The model is stored in app-private storage or a bundled asset and is opened from native code. The Kotlin layer receives bounded text/token events and metrics only.

## Recommended build sequence

1. Install a recent JDK, Android SDK, Android NDK, CMake, Python 3.11+, and the pinned tokenizer/training dependencies.
2. Prepare only legally usable text and instruction data; place it outside the repository or under an ignored data directory.
3. Run tokenizer training and validation, then freeze the vocabulary checksum.
4. Run the model smoke test before a longer pretraining job.
5. Train, instruction-tune, and distill the model using the configurations under `training/`.
6. Convert and quantize the checkpoint using the scripts under `quantization/`.
7. Copy the validated model artifact into the Android app's app-private model delivery path.
8. Build the ARM64 debug APK, test offline behavior, then run the device benchmark harness.
9. Only publish a release artifact after memory, quality, privacy, stability, battery, and thermal gates pass.

## What is not claimed

This repository does not claim frontier-model quality, a measured token-per-second number, a measured 257 MB-device memory result, or a trained checkpoint before those artifacts are actually produced. Device performance depends on the Android version, CPU microarchitecture, thermal state, allocator behavior, background pressure, and selected runtime.

## License and data policy

The application and scripts should ship with an explicit project license. Model weights, tokenizer files, source datasets, teacher outputs, and third-party runtime code must each carry their own license and attribution record. Do not add scraped or copyrighted data without documented permission.

## Open-source license

The source code in this repository is released under the MIT License in `LICENSE`. Training data, model checkpoints, tokenizer artifacts, and third-party runtimes may have separate terms; contributors must preserve provenance and include required attribution. Please open an issue before adding datasets or external weights with unclear licensing.
