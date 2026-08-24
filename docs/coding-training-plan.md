# Mikoo AI coding-agent training plan

## Training objective

The objective is not to make a 354M-parameter model equal to a frontier coding system. The objective is to make it reliable at a bounded set of coding tasks on a 2 GB Android phone: code completion, explanation, unit-test generation, error diagnosis, patch proposal, small refactors, code translation, and repository-context assistance.

## Data composition

The training mixture should combine permissively licensed code with provenance metadata, public task descriptions whose use is permitted, authored examples, and teacher-generated/synthetic examples whose terms are documented. CodeSearchNet is useful for code/docstring and retrieval-style examples across Python, JavaScript, Ruby, Go, Java, and PHP, but source-code licenses remain separate from the repository's tooling license [1]. BigCode's data-governance guidance provides a useful model: preserve provenance, honor original license terms and attribution, and support opt-out/removal workflows [2].

The code mix should cover Python, JavaScript/TypeScript, Kotlin/Java, C++, SQL, HTML/CSS, Bash, JSON, and YAML. Examples must include correct code, intentionally buggy code with fixes, compiler and test logs, API usage, documentation, security review, refactoring, and multilingual natural-language instructions in English, Bengali, and Hindi.

## Data transformations

Every record receives a unique checksum, source/repository/path, license identifier, attribution requirement, language, task type, split, and opt-out status. The pipeline removes credentials, API keys, private keys, access tokens, personal data, malware-like payloads, generated/vendor artifacts where appropriate, minified bundles, duplicated forks, and malformed code. Near-duplicate detection must operate at repository/file/function level to prevent leakage across train and test.

Repository tasks are split by repository and time where possible. A function from the same repository must not appear in both training and evaluation. Test cases and issue descriptions used for evaluation must remain isolated from teacher prompting and student training.

## Distillation workflow

A larger authorized teacher is used only on the training machine. The teacher receives a task and bounded repository context, produces a plan, candidate patch, tests, and explanation, and may be asked to critique or repair its own output. The resulting trajectory is filtered for correctness, safety, license compliance, output length, and reproducibility. The student trains on the final answer plus selected intermediate reasoning artifacts that are safe to retain; hidden chain-of-thought is not required for the mobile product.

The preferred low-cost distillation objective is supervised learning over filtered task/patch/test examples. A controlled hard-example subset may add temperature-scaled logit matching if teacher logits are available and licensing/engineering constraints permit it. The teacher is never packaged with the APK and is never called during offline inference.

## Agent-action training format

The student should learn to emit strict JSON actions matching `model/coding_agent_tools.schema.json`. Training examples must include valid actions, invalid actions with corrections, approval-required write/execute actions, truncated file context, tool errors, failed tests, patch conflicts, and final summaries. The target behavior is to produce a minimal diff and explain uncertainty rather than invent tool success.

## Capability curriculum

| Stage | Examples | Gate |
|---|---|---|
| Code language modeling | Legal code, docstrings, comments, tests, configs | Validation loss improves without language collapse |
| Completion and explanation | Fill functions, explain APIs, annotate code, document modules | Syntax and semantic review improves |
| Test generation | Unit tests, fixtures, edge cases, regression tests | Generated tests run and detect seeded bugs |
| Bug repair | Error logs, failing tests, minimal patches | Patch applies and tests pass |
| Repository context | File search, bounded context selection, multi-file diffs | Relevant files selected within token budget |
| Tool use | JSON actions, approvals, tool errors, cancellation | No unauthorized write/execute action |
| Refinement | Test failure → diagnosis → patch revision | Second attempt improves without regressions |

## Safety and execution boundary

The mobile product may inspect user-selected files and propose patches. Applying a patch requires explicit approval. Running tests or builds requires an allowlisted profile, timeout, output cap, and explicit approval. Arbitrary shell, network access, package installation, credential access, destructive commands, and silent file modification are forbidden. A desktop companion or external sandbox may provide stronger repository-level execution later.

## Evaluation

Short-form evaluation should include syntax/compile checks, unit-test generation, seeded bug repair, diff minimality, code explanation, translation, tool-schema validity, and context retrieval. Repository-level evaluation should include held-out projects and SWE-bench-style tasks, where the patch is applied and repository tests determine success [3] [4]. Results must be reported by language, task, context length, model quantization, and number of refinement attempts.

## References

[1]: https://github.com/github/CodeSearchNet "GitHub CodeSearchNet repository"

[2]: https://www.bigcode-project.org/docs/about/the-stack/ "BigCode The Stack data governance"

[3]: https://www.swebench.com/SWE-bench/ "SWE-bench overview"

[4]: https://www.swebench.com/verified.html "SWE-bench Verified"
