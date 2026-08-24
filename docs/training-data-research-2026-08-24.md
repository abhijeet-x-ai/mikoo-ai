# Mikoo training-data research notes

## Findings

The Stack paper describes a 3.1 TB collection of permissively licensed source code in 30 programming languages and reports that near-deduplication improved results for 350M-parameter decoder-only models. It also documents opt-out and removal processes. This is evidence that permissive code can support training, but it is not permission to copy arbitrary files without retaining file-level provenance.

The Open Source Initiative's data-governance discussion distinguishes data licensing, training permission, and model deployment. It emphasizes that both the collection license and each component/document license matter, that license metadata can be wrong or incomplete, and that automated license detection needs layered verification and human review. Mikoo should therefore ingest only records with source URL, author/owner where available, SPDX-like license evidence, retrieval date, and a rejection reason for ambiguous cases.

The RedPajama NeurIPS 2024 paper describes the value of quality signals and metadata for filtering very large corpora, but its web-only raw data should not be treated as automatically license-safe. Mikoo's default pipeline should prefer public-domain, MIT, Apache-2.0, BSD, CC0, and explicitly verified CC-BY material; it should exclude unknown, proprietary, non-commercial, or ambiguous records unless the owner provides additional permission.

## Design decision

The repository will contain the preparation and validation code, schemas, manifests, and small self-authored smoke-test data only. Large training data and checkpoints remain external to the source repository. Runtime APKs will never download training data, checkpoints, or remote AI models.

## Sources

1. https://arxiv.org/abs/2211.15533 — The Stack: 3 TB of permissively licensed source code.
2. https://opensource.org/ai/webinars/building-public-data-for-llms — Building Public Data for LLMs, Open Source Initiative.
3. https://proceedings.neurips.cc/paper_files/paper/2024/hash/d34497330b1fd6530f7afd86d0df9f76-Abstract-Datasets_and_Benchmarks_Track.html — RedPajama: an Open Dataset for Training Large Language Models.
