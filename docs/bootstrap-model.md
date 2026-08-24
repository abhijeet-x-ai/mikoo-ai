# Mikoo Nano bootstrap model

The Android APK now bundles `android/app/src/main/assets/mikoo_bootstrap.bin`, a 1.58 MB neural checkpoint trained locally from `training/bootstrap_corpus.txt`. The model is a byte-level GRU with 256-token vocabulary, 128-dimensional embeddings, and 256 hidden units. It is intentionally small so the JNI loader and offline generation path can be validated on low-memory phones.

The checkpoint is self-authored and contains no downloaded model weights or external AI dependency. The training command is:

```bash
python3 training/train_bootstrap_gru.py \
  --corpus training/bootstrap_corpus.txt \
  --out android/app/src/main/assets/mikoo_bootstrap.bin \
  --steps 2400 \
  --batch-size 32
```

The binary contract is checked with:

```bash
python3 training/test_bootstrap_checkpoint.py android/app/src/main/assets/mikoo_bootstrap.bin
python3 training/test_bootstrap_generation.py android/app/src/main/assets/mikoo_bootstrap.bin
```

The Android app copies the asset into app-private storage, calls `nativeLoadModel`, and uses the C++ JNI GRU implementation for bounded greedy byte generation. The UI reports `Mikoo Nano local checkpoint loaded; offline inference active.` when the load succeeds.

This is a real local neural bootstrap model, not the planned 353,950,848-parameter production Mikoo coding model. Its corpus is too small for broad code reasoning. Production quality still requires a substantially larger license-audited corpus, tokenizer/data pipeline, long training run, coding evaluations, quantization validation, and a production C++ runtime adapter. No remote model is used as a fallback.
