# Android and JNI integration contract

## RAM contract

The hard application-process ceiling is **749 MB**. The preferred operating target is **650 MB or less** to leave room for Android variation and background memory pressure. The smooth default profile is INT4-group quantization, 512-token context, one inference worker, batch size one, and a 256-token generation cap. The 1,024-token profile is enabled only after real-device validation; 2,048 tokens is stress mode.

## Kotlin responsibilities

Kotlin owns the lightweight text UI, bounded conversation history, lifecycle handling, status presentation, cancellation button, and measured metrics display. It must never deserialize model weights or allocate unbounded transcript content. Conversation history is trimmed by token budget before it crosses the JNI boundary.

## Native responsibilities

C++ owns model loading, tokenizer runtime state, mmap/native buffers, KV cache, scratch/workspace reuse, generation cancellation, token sampling, and native metrics. The native layer must reject oversized paths and prompts, cap generation length, avoid avoidable tensor copies, and release all resources when the activity is destroyed.

## Storage behavior

Storage is expandable and separate from the RAM contract. Only one model may be mapped into the process at a time. Inactive model variants, exported chats, and local knowledge packs remain disk-backed. Conversation history and diagnostic logs use user-configurable quotas, compaction, and rotation. A large disk cache must never be mapped wholesale into RAM.

## Required production JNI API

The prototype exposes status, guarded model loading, cancellation, generation, and a generated-token counter. The production adapter must add a bounded token stream, explicit model close, measured peak/native memory, tokens/sec, first-token latency, and error codes. The adapter must expose model-load failure reasons without leaking paths or secrets.

## Memory-pressure sequence

When measured process memory approaches the 650 MB operating target, stop accepting new generation work, reduce the effective prompt to the configured context, clear and rebuild the KV cache, release temporary buffers, reduce the generation cap, and resume only if the runtime reports safe memory. If the process approaches 749 MB, stop generation and show a clear status rather than forcing the process to continue.

## Runtime replacement point

Replace the guarded `nativeLoadModel` and `nativeGenerate` branches in `android/app/src/main/cpp/mikoo_jni.cpp` with the validated GGUF-compatible or ExecuTorch implementation after the model checkpoint and quantized artifact are available. The first runtime experiment must be evaluated on ARM64 Android in airplane mode.
