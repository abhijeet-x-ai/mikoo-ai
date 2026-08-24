# Mikoo tokenizer pipeline

Mikoo starts with compact raw-text subword tokenization for English, Bengali, and Hindi. Train BPE and unigram candidates at 8,192, 12,288, and 16,384 vocabulary sizes using the cleaned multilingual corpus. Keep the tokenizer with the best joint result across Bengali/Hindi/English token fertility, unknown-token rate, vocabulary file size, script coverage, mixed-script handling, code handling, and held-out language-model validation.

## Required checks

The tokenizer test suite must cover Unicode normalization, Bengali conjuncts and diacritics, Devanagari combining marks, punctuation, digits, Latin/Bengali/Hindi mixed text, chat template markers, code snippets, and empty/very long inputs. Every test must verify encode/decode round trips and deterministic output.

## Data policy

Each source must have a license manifest, attribution, language label, and collection date. The pipeline must normalize Unicode, remove malformed text, filter extreme lengths and low-quality boilerplate, exact-deduplicate and near-deduplicate, reduce personally identifying information where appropriate, filter toxic/unsafe training content, check evaluation contamination, and write deterministic train/validation/test manifests.

## Export contract

The exported tokenizer must include a checksum, vocabulary size, special-token map, normalization configuration, model type, source-data manifest hash, and chat-template version. The Android runtime must load only the compact runtime representation needed for encoding and decoding.
