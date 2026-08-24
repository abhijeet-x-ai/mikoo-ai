# Mikoo quantization pipeline

The quantization stage begins only after the tokenizer checksum, architecture manifest, and trained checkpoint are frozen. Produce three candidates: INT8 reference, INT4 group candidate, and mixed precision. The preferred release is the smallest candidate that passes multilingual quality, stability, and memory gates.

## Required sequence

1. Validate the FP32/BF16 checkpoint and compare a deterministic host inference reference.
2. Convert to the selected native interchange format and verify tensor names, shapes, tied embeddings, RoPE configuration, vocabulary checksum, and special tokens.
3. Quantize INT8 and INT4-group candidates using a representative calibration set containing English, Bengali, Hindi, mixed-script text, code, short prompts, and long prompts within the supported context.
4. Add model metadata: architecture, exact parameter count, context, quantization scheme, calibration-manifest hash, source-license manifest, runtime version, and checksum.
5. Compare held-out perplexity and task outputs against the unquantized checkpoint.
6. Run deterministic generation, cancellation, context truncation, malformed-input, and long-generation tests.
7. Measure actual model file size and Android peak PSS/RSS; do not infer runtime RAM from file size.

## Release gate

A candidate is releasable only if all tensors are present, checksums match, dequantization sanity checks pass, quality regression is within the configured threshold, and the Android build operates offline without exceeding the 749 MB hard peak application-RAM ceiling, with a preferred operating target of 650 MB or less.
