# Mikoo 8,000-step retraining run — 2026-08-24

## Training input and command

The run used the self-authored, license-safe `training/bootstrap_corpus.txt` containing 9,758 bytes of structured English and Bengali coding examples. No network data or external AI service was used.

The trainer was optimized to use a precomputed sliding-window view for lower batch-construction overhead. The successful command was:

```bash
python3 training/train_bootstrap_gru.py \
  --corpus training/bootstrap_corpus.txt \
  --out /tmp/mikoo_bootstrap_8000.bin \
  --steps 8000 \
  --batch-size 32 \
  --seed 20260824
```

Progress reached step 8,000 and exported a 1,580,056-byte checkpoint. Loss values included `0.30109` at step 200, `0.04458` at step 1,200, `0.04066` at step 2,400, `0.04230` at step 5,000, `0.03715` at step 6,000, and `0.04322` at step 8,000. The final checkpoint SHA-256 is `9ac171603ece6670eb7e75deccfa8158c108ea612e4070b8214918044a25e4fb`.

## Validation

Checkpoint integrity passed. The coding and Bengali acceptance suite passed all 5 cases. Generation smoke tests returned valid local responses for greeting, bug-fix, testing, review, Python, Kotlin, C++17, README, and Bengali prompts under the 768-unit output bound.

The checkpoint was copied identically to `android/app/src/main/assets/mikoo_bootstrap.bin` and `desktop/models/mikoo_bootstrap.bin`. The Linux Tauri package was rebuilt and installed over the prior desktop build. Desktop Rust tests passed 2/2.

## Real desktop interaction

After restarting the installed app to force model reload, a real UI prompt — `Write a Python function to safely divide two numbers` — produced a visible local response containing a safe-divide Python function, zero-division handling, and test guidance. The UI showed `REPLIED`, `Offline local model`, and `history saved locally`. The observed sandbox process RSS was approximately 164 MB; this is not a cross-device benchmark.

## Boundary

This remains the small real local bootstrap model, not the planned 354M student or 6B teacher. More steps do not transform a small corpus/model into a production-scale coding model; larger license-audited data, a larger architecture, GPU training, distillation, quantization, and broader evaluation are still required.
