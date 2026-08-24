# Mikoo AI release checklist

## Model

The release package contains the exact model specification, tokenizer checksum, quantized model checksum, model card, data card, license notices, and a clear statement of measured versus estimated behavior. The model has passed held-out English, Bengali, Hindi, translation, summarization, instruction, safety, and quantization-regression tests.

## Android

The ARM64 release APK builds reproducibly with the documented SDK/NDK and CMake versions. It contains no INTERNET, storage, or microphone permission unless a later feature has a separately reviewed requirement. The model is loaded in native memory, generation runs off the main thread, cancellation works, old history is bounded, and lifecycle transitions do not leak native resources.

## Device evidence

A physical low-end Android device has been tested in airplane mode at 128, 256, and 512 tokens. The report includes measured model size, APK size, load time, first-token latency, tokens/sec, peak and average PSS/RSS, native and managed heap, CPU, battery, temperature, crash/ANR rate, cancellation, and offline success. Any estimate is labeled as an estimate and includes a replacement measurement method.

## Privacy and safety

No network access is required after installation, no cloud credentials are bundled, telemetry is disabled by default, local conversation handling is documented, and basic unsafe-request regression tests pass for the supported scope. The limitations are shown to users rather than hidden behind optimistic performance claims.
