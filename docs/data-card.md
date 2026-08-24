# Mikoo AI data card

## Data scope

The training corpus is intended to cover English, Bengali, and Hindi general language, grammar, basic knowledge, instructions, conversations, question answering, summarization, rewriting, translation, basic reasoning, and limited coding examples. The final corpus size is not fixed until tokenizer fertility, validation loss, licensing, and compute budget are reviewed.

## Collection and licensing

Every source must be recorded in a manifest with source name, URL or identifier, license, permitted use, collection date, language, transformation steps, and checksum. Datasets with unclear licensing, prohibited redistribution, or incompatible terms must be excluded. Teacher-generated examples must carry a record of the teacher's authorization/terms and the generation configuration.

## Processing

The reproducible pipeline performs NFKC normalization, control-character removal, URL placeholder normalization, whitespace normalization, malformed-record rejection, length filtering, exact deduplication, deterministic shuffling and splitting, and source attribution. Production training must add reviewed language identification, near-duplicate detection, personally identifying information reduction, toxicity/unsafe-content filtering, quality scoring, and evaluation-contamination checks. The included stdlib utility intentionally does not pretend to implement the policy-sensitive PII and toxicity steps.

## Splits and evaluation

The planned default split is 98% train, 1% validation, and 1% test with a fixed seed. Splits must be stratified or audited by language and task so that Bengali and Hindi are not hidden by an English-heavy aggregate score. Held-out evaluation data must be isolated from training and distillation prompts.

## Risks

Small multilingual datasets may encode social bias, dialect imbalance, factual errors, unsafe instructions, and repetitive artifacts. Filtering can also remove legitimate dialect or safety-research examples. All filtering thresholds must be documented, and qualitative review must accompany automated metrics.
