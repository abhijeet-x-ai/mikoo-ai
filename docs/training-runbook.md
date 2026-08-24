# Mikoo AI training runbook

## Status

The revised target is a 353,950,848-parameter model with a 749 MB hard application-RAM cap and 512-token default context. The sandbox currently has no detected PyTorch installation and no NVIDIA GPU toolchain. Therefore no model checkpoint or trained weights are claimed in this repository. The runbook is prepared for execution on a machine with the required ML dependencies and a CUDA-capable GPU or rented GPU time.

## Stage order

First build and validate the tokenizer on a legally reviewed corpus. Then run a short smoke pretraining job to verify data loading, loss decrease, checkpoint restore, and validation by language. Only after the smoke run passes should the 500M-token bootstrap job be attempted. A fuller 1.44B-token run is optional and should be justified by held-out improvements per unit of compute.

After pretraining, run instruction tuning on curated English/Bengali/Hindi tasks. Use teacher-generated supervision or authorized teacher logits only during training. Filter teacher outputs, preserve language balance, remove malformed outputs, and evaluate on prompts excluded from both teacher prompting and student training. Finally convert, quantize, and validate INT8, INT4-group, and mixed-precision artifacts.

## Hardware and storage

CPU-only data preparation is acceptable. Pretraining and distillation require a CUDA-capable GPU or rented GPU time; the required VRAM depends on optimizer, sequence length, microbatch, gradient checkpointing, and precision. The final Android device is for inference benchmarking, not for training. The preferred 2 GB-device profile is INT4-group, 512-token context, one inference worker, and a 256-token generation cap. Keep multiple checkpoints, tokenizer artifacts, optimizer state, and cleaned data outside the Android package and record checksums in manifests.

## Required logs

Every run records the git revision, model-spec checksum, tokenizer checksum, data manifest hash, seed, language sampling policy, token count, sequence length, optimizer, learning rate, precision, checkpoint interval, validation losses by language, task scores, quantization results, and failure reasons. No run is considered reproducible if these fields are missing.

## Distillation protocol

Use a larger authorized teacher to generate short, high-quality examples for the supported tasks. Store prompt, output, language, task, safety label, source/license record, and teacher configuration. The student uses a supervised loss on filtered teacher answers and may use temperature-scaled logit matching on a small hard-example subset. The teacher is never packaged with, called by, or required by the Android application.
