# Mikoo AI model card

## Model identity

Mikoo AI Medium Multilingual v0.2 is a planned **353,950,848-parameter** decoder-only Transformer for offline Android text generation. The architecture uses 24 layers, hidden size 1,152, 18 query heads, two KV heads, SwiGLU, RMSNorm, RoPE, tied embeddings, a 24,576-token English/Bengali/Hindi vocabulary, and no projection bias.

## Intended use

The model is intended for basic offline conversation, question answering, rewriting, summarization, translation between English/Bengali/Hindi, simple reasoning, and limited coding assistance. It is not intended for medical, legal, financial, emergency, high-stakes, or frontier-quality use. It should not be treated as a factual authority or as a replacement for professional advice.

## Deployment target

The hard application-process target is **749 MB peak RAM**. The smooth default profile for a 2 GB phone is INT4-group quantization, 512-token context, one inference worker, batch size one, bounded history, and a 256-token generation cap. A 1,024-token profile is recommended only after physical-device validation; 2,048 tokens is a stress mode.

The planned INT4-group weight footprint is approximately 199.1 MB including a small metadata allowance. Conservative estimated peak application memory is approximately 525.4 MB at 512 tokens, 531.7 MB at 1,024 tokens, and 544.3 MB at 2,048 tokens. These are calculations/estimates, not device measurements. The operational target is 650 MB or less even though the hard cap is 749 MB.

## Storage policy

Storage is expandable and is not treated as a 5 GB hard limit. Multiple model variants, exported conversations, local knowledge packs, and disk-backed caches may use more storage. The application should load only one model at a time, use user-configurable history/cache quotas, rotate logs, compact conversation records, and provide cleanup controls. Storage growth must not be allowed to cause unbounded RAM mapping.

## Training status

This repository contains the updated architecture specification, training entry point, quantization plan, and Android prototype. It does not contain a trained checkpoint. Capability, accuracy, safety behavior, and generation quality must not be inferred from this card until training and held-out evaluations are complete.

## Known limitations

A model of this size will have a limited factual memory and lower reasoning reliability than larger assistants. Bengali and Hindi quality depends strongly on data mix and tokenizer allocation. Quantization may cause additional degradation. Outputs may be incorrect, incomplete, repetitive, or unsafe; downstream applications must show limitations clearly.

## Evaluation requirements

Before release, report held-out perplexity and task results by language, translation accuracy, summarization quality, refusal/safety regression results, model file size, first-token latency, tokens/sec, peak and average PSS/RSS, CPU utilization, battery drain, temperature, crash/ANR rate, and offline behavior on actual 2 GB Android devices.
