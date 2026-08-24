# Mikoo high-data pretraining and advanced coding-agent plan

## Scope

Mikoo will be trained as its own decoder-only coding model. The Android APK will contain only Mikoo-owned local artifacts and a native inference runtime. A training-time teacher or remote data source is never called by the APK.

The production architecture remains the 353,950,848-parameter decoder-only Transformer specified in `model/model_spec.json`: 24 layers, hidden size 1,152, 18 query heads, 2 KV heads, SwiGLU, RMSNorm, RoPE, tied embeddings, and a 24,576-token vocabulary. The default mobile profile remains INT4 group quantization, 512-token context, batch size 1, and one inference worker. The Android RAM target is a hard peak of 749 MB with a preferred peak of 650 MB.

## High-data mixture

The ingestion pipeline should combine four separately manifested streams: file-level code from explicitly verified permissive or public-domain sources; code documentation and tests from the same repositories; authored instruction/patch trajectories created by the Mikoo project; and evaluation-only repositories that never enter training. Each record retains its original source URL, repository, path, commit, retrieval date, license evidence, attribution requirement, language, task type, and checksum.

The first production mixture should prioritize Python, JavaScript/TypeScript, Kotlin/Java, C++, SQL, HTML/CSS, Bash, JSON, and YAML. The coding curriculum should move from syntax and completion to explanation, tests, seeded bug repair, refactoring, repository context, safe tool actions, and failed-test refinement. English, Bengali, and Hindi instructions should be represented deliberately instead of being inferred from a web-scale crawl.

## Governance gates

A record is rejected if its file-level license is missing, ambiguous, proprietary, non-commercial, or contradicted by repository metadata. The default allowlist is public domain/CC0, MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, Unlicense, and explicitly reviewed CC-BY. License metadata is not inferred from a dataset-level label. Credentials, private keys, access tokens, personal contact data, generated/vendor bundles, minified files, and malware-like samples are removed or rejected. Exact and near-duplicate filtering occurs before repository-level train/validation/test splitting.

This governance approach follows the distinction between collection licensing and component/document licensing described by the Open Source Initiative [1]. The Stack research demonstrates that a permissively licensed, near-deduplicated code mixture can support 350M-parameter decoder experiments [2], while the RedPajama work reinforces the value of quality signals and provenance metadata for large-scale filtering [3]. These sources are evidence for a pipeline design, not permission to copy arbitrary online data.

## Training stages

| Stage | Data | Objective | Exit gate |
|---|---|---|---|
| 0. Bootstrap | Self-authored examples | Byte-level local model smoke test | Native load, generation, cancellation, and checksum tests pass |
| 1. Code language modeling | License-audited code/docs/tests | Causal language modeling | Validation loss improves without language collapse |
| 2. Coding instruction tuning | Authored and permissioned task/patch/test records | Supervised instruction tuning | Syntax, test, and structured-output checks pass |
| 3. Agent trajectory tuning | Plans, bounded tool calls, diffs, tool results, failures | Safe action and refinement behavior | No unauthorized write/execute action; valid schema output |
| 4. Mobile conversion | Quantized checkpoint and tokenizer | Calibration and runtime optimization | Peak PSS remains below 749 MB on target devices |

## Feasibility of the current environment

The current sandbox exposes 6 CPU cores, approximately 3.8 GiB RAM, 2 GiB swap, about 27 GiB free disk, and no NVIDIA GPU. It can train and validate the small bootstrap checkpoint, build the data pipeline, and run short CPU smoke tests. It cannot realistically perform high-data pretraining of the 354M production architecture in a useful time or memory envelope. A serious run requires a separate CUDA-capable training machine or a user-provided persistent training environment; the resulting checkpoint can then be converted and tested locally without placing any remote dependency in the APK.

## Agent behavior target

The production student should emit a plan, bounded context request, patch proposal, test proposal, and final summary using `model/coding_agent_tools.schema.json`. A coordinator can launch independent internal subtasks for repository mapping, diagnosis, implementation, and verification, but all writes and executions remain approval-gated. The mobile app should never claim a tool succeeded unless the local result is available and checksummed.

## References

[1]: https://opensource.org/ai/webinars/building-public-data-for-llms "Open Source Initiative: Building Public Data for LLMs"
[2]: https://arxiv.org/abs/2211.15533 "The Stack: 3 TB of permissively licensed source code"
[3]: https://proceedings.neurips.cc/paper_files/paper/2024/hash/d34497330b1fd6530f7afd86d0df9f76-Abstract-Datasets_and_Benchmarks_Track.html "RedPajama: an Open Dataset for Training Large Language Models"
