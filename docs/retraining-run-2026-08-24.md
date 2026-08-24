# Mikoo retraining run — 2026-08-24

## Input

The run used the repository's self-authored `training/bootstrap_corpus.txt`. The corpus contained 9,758 bytes across 258 records/lines of structured English and Bengali examples covering Python, Kotlin, C++17, JavaScript, SQL, Bash, README writing, testing, safe patch proposals, and local-agent safety behavior. No network data or external AI service was used during training.

## Training

`training/train_bootstrap_gru.py` was run on CPU with seed `20260824`, 1,200 steps, and batch size 32. The final reported loss was `0.04935`. The exported byte-level GRU checkpoint is 1,580,056 bytes and has SHA-256 `2584d347d4ea87e9e99b750b5902950375e30ff7e8aa072666a5ff286a400854`. The same checkpoint was copied to the Android asset path and desktop model resource path.

A longer 8,000-step attempt was stopped after more than eight minutes because it exceeded the sandbox's practical CPU execution window. It did not overwrite the previous artifact; the bounded 1,200-step run completed and produced the artifact used below.

## Evaluation

Checkpoint integrity passed. The coding/Bengali acceptance suite passed all 5 cases. The generation smoke test returned 85 units for `Hello`, 129 for bug fixing, 65 for test-context requests, 346 for a Python function, 233 for a Kotlin function, 290 for a C++17 function, and 354 for a README request under the 768-unit limit.

The Linux Tauri desktop package was rebuilt and installed. A real UI interaction with `Write a Python function to safely divide two numbers` displayed a local response with a zero-division guard and test guidance. The application showed `REPLIED` and `history saved locally`. The observed sandbox process RSS was approximately 166 MB; this is not a cross-device benchmark.

## Limitations

This is a retrained bootstrap model, not the planned 354M mobile student or 6B teacher. The current corpus and CPU-only environment are insufficient for high-data production pretraining. A production model requires a larger license-audited corpus, GPU training, tokenizer work, distillation/evaluation, quantization, and device testing.
