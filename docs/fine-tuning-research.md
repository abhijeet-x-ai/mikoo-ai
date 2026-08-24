
## Official dataset findings

OpenCodeInstruct's Hugging Face dataset card identifies it as a code-focused instruction-tuning dataset with approximately 4.97 million rows, structured fields such as input/output/domain/generation metadata and test metrics, and a `cc-by-4.0` dataset license. It may be useful as a candidate source, but Mikoo must verify the card, content provenance, attribution requirements, and downstream redistribution conditions at the time of use. Source: https://huggingface.co/datasets/nvidia/OpenCodeInstruct

CodeSearchNet's official repository describes approximately 2 million comment/code pairs from open-source libraries, with code in Python, JavaScript, Ruby, Go, Java, and PHP. It uses JSONL records containing language, repository/path, code, docstring, and partition metadata; the repository tooling is MIT-licensed, but the source code used as data has its own license files. Source: https://github.com/github/CodeSearchNet

SWE-bench's official pages describe repository-level issue resolution where a model receives a codebase and issue, generates a patch, and is evaluated by applying the patch and running tests. SWE-bench Verified is a human-validated subset of 500 instances. Sources: https://www.swebench.com/SWE-bench/ and https://www.swebench.com/verified.html
