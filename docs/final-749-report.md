# Mikoo AI — Revised final report

## Clarified requirement

The 5 GB value is no longer a hard storage ceiling. Mikoo may use expandable storage for the model, multiple model variants, conversation history, exports, and disk-backed caches. The hard runtime constraint is **749 MB maximum application-process RAM**, with a smooth default profile on a **2 GB RAM Android phone**.

Storage growth and RAM growth are separate. The application will load only one active model into native memory, keep inactive models and history on disk, compact/rotate persistent data, and provide user-controlled cache cleanup. A large storage allowance must never be interpreted as permission to map all stored data into RAM.

## Revised model target

The updated architecture target is **353,950,848 parameters**:

| Component | Configuration |
|---|---:|
| Vocabulary | 24,576 English/Bengali/Hindi subword tokens |
| Layers | 24 |
| Hidden size | 1,152 |
| Query heads | 18 |
| KV heads | 2 |
| Head dimension | 64 |
| Feed-forward | SwiGLU, intermediate 3,072 |
| Normalization | RMSNorm |
| Position encoding | RoPE |
| Embeddings | Tied input/output |
| Default context | 512 tokens |
| Recommended context | 1,024 tokens |
| Stress context | 2,048 tokens |
| Primary quantization | INT4 group |

The exact parameter calculation is recorded in `mikoo-ai/model/model_spec.json` and validated by the project tests. The preferred INT4-group raw quantized-weight estimate is approximately **199.1 MB**; including the planning metadata allowance, the application budget uses **201.1 MB**. INT8 is retained as a quality/compatibility reference at approximately 354 MB theoretical weights; FP16 is not recommended as the default because it leaves too little room for runtime overhead on a 749 MB cap.

## RAM profiles

| Profile | Quantization | Context | Generation cap | Estimated peak application RAM | Status |
|---|---|---:|---:|---:|---|
| Smooth default | INT4-group | 512 | 256 tokens | 525.4 MB | Calculated estimate; target for 2 GB phones |
| Balanced | INT4-group | 1,024 | 384 tokens | 531.7 MB | Calculated estimate; enable after device test |
| Stress | INT4-group | 2,048 | 512 tokens | 544.3 MB | Calculated estimate; developer/benchmark mode |
| Quality fallback | INT8 | 512 | 256 tokens | 680.2 MB | Calculated estimate; only if quality gain is worth the cost |

The operational target is **650 MB or less**, despite the hard cap of 749 MB. The extra margin is required because real Android PSS/RSS depends on allocator behavior, thread stacks, runtime workspace, page residency, background pressure, thermal state, and Android version. These values are not physical-device measurements.

## Storage policy

Storage is expandable and may exceed 5 GB if the user chooses to keep additional models, local knowledge packs, exported conversations, or diagnostic data. The application will use one active model at a time, disk-backed conversation records, compaction, configurable quotas, rotating logs, a free-space check, and explicit cache cleanup. Storage may grow; RAM must remain bounded.

## Completed implementation artifacts

The project contains the revised model manifest, training configuration, PyTorch architecture trainer, multilingual data-cleaning utility, tokenizer plan, quantization plan, Kotlin chat UI prototype, C++/JNI bridge, Android build files, benchmark harness, model/data cards, RAM policy, tests, and the regenerated calculation chart and CSV tables.

The C++ bridge is intentionally guarded: it does not fabricate answers before a real trained model and validated runtime are connected. The remaining integration point is to replace the guarded loader/generation branch with the selected GGUF-compatible INT4 runtime or the validated ExecuTorch/XNNPACK INT8 path.

## Validation status

The following sandbox checks pass after the revision: exact model-manifest parameter validation, revised context/RAM policy validation, training configuration structural validation, benchmark-template generation, Android manifest offline-permission validation, Python syntax checks, and presence checks for Kotlin/JNI sources.

The sandbox still has no detected Android SDK/Gradle/ADB toolchain, PyTorch installation, CUDA GPU, or physical 2 GB Android device. Therefore no trained checkpoint, quantized model artifact, APK, tokens/sec, battery, thermal, crash-rate, or real-device RAM number is claimed.

## Required next execution

On a training/build machine, install the Android SDK/NDK/CMake/Gradle toolchain and PyTorch, provide legally reviewed English/Bengali/Hindi data, train the tokenizer and model, run instruction tuning and distillation, quantize INT4-group and INT8 artifacts, connect the validated runtime in `mikoo_jni.cpp`, build the ARM64 APK, and run the benchmark harness on an actual 2 GB phone in airplane mode at 512, 1,024, and 2,048-token settings.

Release only if the default profile is smooth and stable, peak process memory remains below 749 MB and preferably below 650 MB, the app works offline, and the measured quality/latency tradeoff is documented honestly.
