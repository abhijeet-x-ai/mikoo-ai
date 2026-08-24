# Mikoo AI coding-agent fine-tuning dataset plan

## Executive recommendation

Mikoo AI should be fine-tuned as a **focused coding agent**, not as a generic chatbot with a few code examples added. The most valuable data is not only raw source code; it is the complete engineering loop: a natural-language request, bounded repository context, a plan, a minimal patch, tests, compiler/test feedback, a correction, and an honest final report.

The recommended dataset should combine three sources: provenance-preserving licensed code and documentation, authored task examples, and filtered teacher-generated trajectories. CodeSearchNet is a useful source for code/docstring and retrieval-style examples across Python, JavaScript, Ruby, Go, Java, and PHP, but its tooling license does not replace the licenses of the source repositories [1]. NVIDIA's OpenCodeInstruct is a candidate source for code instruction tuning and is labeled `cc-by-4.0` on its Hugging Face card, but the exact dataset version, provenance, attribution obligations, and redistribution terms must be checked before use [2]. BigCode's governance guidance is a good operational model: retain provenance, honor original license terms and attribution, and support opt-out/removal handling [3].

## Target skills

| Skill | What the dataset must teach | Priority |
|---|---|---:|
| Code completion | Complete functions, classes, imports, types, configs, and small modules | High |
| Code explanation | Explain behavior, complexity, APIs, assumptions, and failure modes | High |
| Unit-test generation | Produce unit, integration, regression, property-based, and edge-case tests | High |
| Debugging | Interpret compiler errors, stack traces, failing assertions, and logs | High |
| Bug fixing | Make the smallest patch that resolves a reproducible failure | Very high |
| Refactoring | Improve structure, readability, performance, or typing without changing behavior | High |
| Code translation | Translate between Python, TypeScript/JavaScript, Kotlin/Java, C++, and SQL | Medium |
| Repository context | Select relevant files and avoid irrelevant or secret-bearing context | Very high |
| Tool use | Emit valid JSON actions, request approval, and report actual tool results | Very high |
| Security-aware coding | Avoid secrets, unsafe shell, injection, insecure defaults, and malicious payloads | High |
| Planning and reporting | Explain changed files, tests, risks, and remaining uncertainty | Very high |

## Recommended dataset mixture

The percentages below apply to the **fine-tuning mixture**, not necessarily to the raw downloaded corpora. Each source must be converted into the common Mikoo record format, deduplicated, filtered, and reweighted.

| Dataset family | Share | Main purpose |
|---|---:|---|
| Code completion and code-language SFT | 15% | Syntax, idioms, APIs, imports, types, and local completion |
| Code explanation and documentation | 10% | Accurate explanations, comments, docstrings, and README content |
| Unit-test and regression-test generation | 15% | Tests, fixtures, edge cases, mocks, and bug-detection behavior |
| Bug fixing and patch generation | 15% | Issue-to-diff behavior and minimal repair |
| Error diagnosis and compiler/test feedback | 10% | Stack traces, logs, failing tests, and repair reasoning |
| Refactoring and behavior preservation | 10% | Safe transformations with regression checks |
| Repository-context and code search | 10% | File selection, symbol lookup, dependency tracing, and context compression |
| Tool-use and approval trajectories | 8% | Valid action JSON, approvals, cancellation, errors, and honest reports |
| Security and safe coding | 4% | Secret removal, injection prevention, dependency hygiene, and refusal boundaries |
| Multilingual coding instructions | 3% | Bengali/Hindi/English requests over the same coding skills |
| **Total** | **100%** | |

The mixture should be sampled by task difficulty. Begin with short single-file tasks, then add multi-file patches, test feedback, and bounded repository context. Do not let easy code completion dominate the training signal; it creates a fluent model that still fails at debugging and tool use.

## Source portfolio

| Source type | Recommended use | Governance requirement |
|---|---|---|
| Authored examples | High-quality Bengali/Hindi/English instructions, Android/Kotlin examples, safety cases, and product-specific response style | Keep copyright and contributor consent records |
| Permissively licensed repositories | Code completion, documentation, tests, and real bug-fix examples | Preserve repository, path, commit, SPDX license, attribution, and checksum |
| CodeSearchNet-derived records | Code/docstring alignment and retrieval-style training | Keep source-language license files and repository provenance [1] |
| OpenCodeInstruct-derived records | Candidate instruction-tuning examples | Verify exact card/version, `cc-by-4.0` obligations, provenance, and downstream redistribution before inclusion [2] |
| Issue/patch datasets | Bug fixing, regression tests, and issue-to-diff tasks | Keep issue/commit provenance; isolate evaluation instances |
| Teacher-generated data | Tool trajectories, multilingual tasks, hard negatives, and repair attempts | Record teacher identity, terms, prompt, seed/settings, filter decisions, and human/programmatic verification |
| User-contributed tasks | Product-specific coding style and real failure modes | Obtain explicit contribution terms and remove secrets/private data |

A source should be rejected when its license is missing or unclear, its provenance cannot be reconstructed, its opt-out status is unknown where an opt-out process exists, or its examples contain credentials, private information, malicious payloads, or redistribution restrictions incompatible with the intended release.

## Programming-language mixture

Use the following initial programming-language distribution, then adjust it based on held-out quality and actual user demand:

| Language family | Share of code examples |
|---|---:|
| Python | 24% |
| JavaScript/TypeScript | 20% |
| Kotlin/Java | 16% |
| C/C++ | 12% |
| SQL | 8% |
| HTML/CSS | 6% |
| Bash and shell configuration | 4% |
| JSON/YAML/TOML | 4% |
| Go/Rust/PHP/Ruby/other | 6% |
| **Total** | **100%** |

The model's natural-language instruction distribution should be approximately **45% English, 27.5% Bengali, and 27.5% Hindi** in the multilingual task portion, with code comments and identifiers left in their source language. Bengali and Hindi prompts should include debugging, tests, refactoring, and repository tasks rather than only translation tasks.

## Record format

Every record should conform to `training/code_record.schema.json`. At minimum it contains:

```json
{
  "record_id": "repo_commit_path_task_hash",
  "task_type": "bug_fixing",
  "language": "python",
  "prompt": "Fix the failing parser when the input ends with a trailing comma.",
  "context": "<bounded selected files and relevant test>",
  "response": "<explanation and/or final answer>",
  "patch": "<unified diff>",
  "test_log": "<bounded actual result>",
  "tool_actions": [],
  "license": "MIT",
  "source": "licensed_repository_or_authored",
  "repository": "example/project",
  "path": "src/parser.py",
  "attribution": "Required attribution text, if any",
  "content_sha256": "64-character checksum",
  "opt_out_status": "not_requested",
  "split": "train",
  "teacher": "none",
  "teacher_terms_record": "none"
}
```

For a tool trajectory, include the action request, approval state, actual tool result, errors, and final state. A failed attempt is valuable only when the failure is real, bounded, and paired with a correct diagnosis or repair. Never train the model to say that a test passed when the record contains no successful test result.

## Fine-tuning curriculum

### Stage 0: Data and tokenizer adaptation

Before supervised fine-tuning, continue code-language modeling on a clean, license-reviewed corpus. Mix source code with docstrings, READMEs, tests, issue descriptions, API documentation, compiler messages, and configuration files. Keep the 24,576-token multilingual tokenizer candidate, but compare it against 16,384 and 32,768 candidates using fertility, unknown rate, Bengali/Hindi script coverage, code punctuation handling, and validation loss.

### Stage 1: Basic coding SFT

Use completion, explanation, documentation, test generation, translation, and short debugging examples. A planning target is **10–30 million high-quality tokens**, repeated for a small number of epochs only if validation quality improves. Use packed sequences where possible, but retain complete examples and do not split a patch from its test result across unrelated records.

### Stage 2: Repair and test SFT

Add **20–50 million tokens** of issue-to-patch, failing-test-to-repair, compiler-error-to-fix, and regression-test examples. This stage should be weighted more heavily than generic completion because it most directly improves agent usefulness. Include both successful and rejected patches, with the rejection reason made explicit.

### Stage 3: Repository-context and tool-action tuning

Add **5–15 million tokens** of bounded repository tasks. The model learns to list/search/read only relevant files, compress context, propose a diff, request approval, process a tool result, and produce a final report. Train valid and invalid JSON actions, approval-required writes, timeouts, cancellation, patch conflicts, and tool errors.

### Stage 4: Teacher distillation and preference filtering

Use a larger authorized teacher to produce candidate plans, patches, tests, critiques, and repair trajectories. Keep only examples that pass programmatic checks and, for a sample, human review. Prefer supervised distillation over hidden reasoning imitation: train on concise plans, observable actions, patches, test results, and final explanations. Use preference pairs such as minimal-passing patch versus large-regression patch, truthful report versus fabricated-success report, and secure implementation versus insecure implementation.

### Stage 5: Quantization-aware acceptance

Train or calibrate INT8 and INT4-group candidates and compare them with the unquantized checkpoint. The smallest model variant should be released only when it passes code syntax, compile/test, tool-schema, safety, multilingual, and Android memory gates. Quantization is an acceptance stage, not a substitute for better data.

## Data quality pipeline

The preparation pipeline should run in the following order:

1. Verify the source manifest, license, attribution, repository commit, and opt-out state.
2. Normalize Unicode, line endings, language labels, and code fences without altering executable semantics.
3. Remove secrets, private keys, access tokens, personal data, malicious or exploit-focused payloads, generated bundles, vendored dependencies, minified files, and binary blobs.
4. Parse or compile code where a safe parser/compiler is available. Record failures rather than silently treating malformed code as positive data.
5. Remove exact duplicates and near duplicates at repository, file, function, and prompt level.
6. Detect contamination against validation and test repositories, benchmark prompts, public reference answers, and teacher prompts.
7. Check task/response alignment: the patch must touch the requested behavior, the tests must relate to the task, and the explanation must not contradict the diff.
8. Apply length and context bounds compatible with 512-token default, 1,024-token recommended, and 2,048-token stress inference.
9. Score examples for correctness, minimality, security, language quality, and tool honesty.
10. Write an immutable manifest and checksum for every released data shard.

## Splitting strategy

Split by repository and project family, not by random record. A repository, fork, mirrored package, or copied benchmark task must not appear in more than one split. Keep at least three evaluation partitions:

| Split | Purpose |
|---|---|
| Train | Model fitting and teacher distillation |
| Validation | Hyperparameters, mixture weights, early stopping, and quantization selection |
| Test | Final locked comparison; never used to prompt the teacher or tune the model |
| Device smoke set | Small local tasks for Android latency, memory, cancellation, and offline behavior |
| Repository holdout | Unseen multi-file tasks for context selection and patch quality |

The repository-level test should include real patch application and test execution. SWE-bench evaluates real GitHub issues by applying generated patches and running repository tests [4], while SWE-bench Verified is a human-validated subset of 500 instances [5]. Use these as external evaluation references; do not train on their test prompts or hidden patches.

## Evaluation gates

| Gate | Minimum requirement before moving forward |
|---|---|
| Syntax/compile | No regression on the locked language-specific smoke set |
| Unit tests | Generated tests run, cover the requested behavior, and detect seeded defects |
| Bug fixing | Patch applies cleanly and relevant tests pass on held-out tasks |
| Refactoring | Existing behavior remains correct and diff stays scoped |
| Tool protocol | 100% schema validity on the required action subset; writes/execution always require approval |
| Truthfulness | No fabricated file reads, patch applications, or test successes in sampled audits |
| Multilingual | No severe regression in Bengali/Hindi instruction following or code-related comprehension |
| Security | Secrets and dangerous-operation tests are rejected or safely redirected |
| Mobile memory | Default INT4 profile stays below the 749 MB hard cap and preferably below 650 MB on the target device |
| Mobile usability | Measure first-token latency, tokens/sec, cancellation, thermal behavior, battery, crashes, and ANRs on a real 2 GB phone |

Short-form benchmarks such as HumanEval/MBPP-style tasks are useful for fast iteration but are not sufficient to establish repository-level coding ability. The project should report them alongside patch application, test outcomes, repository context, tool use, multilingual behavior, and mobile measurements.

## Recommended first dataset release

For the first reproducible Mikoo dataset release, begin with a smaller, auditable corpus rather than attempting to ingest every public code dataset:

| Component | Initial target |
|---|---:|
| Licensed/authored code and documentation | 40–50% of fine-tuning records |
| Verified issue/patch/test records | 20–25% |
| Teacher-generated and synthetic records | 25–35% |
| Multilingual authored/translated instructions | At least 10% of all task prompts, overlapping the categories above |
| Tool-action records | At least 8% of all task records, overlapping the categories above |

The release should contain a dataset card, source manifest, license/attribution table, filtering report, split manifest, checksums, known limitations, and an opt-out contact. Do not publish raw source files whose licenses do not permit redistribution; publish metadata or transformation instructions where necessary.

## Final recommendation

The most important investment is **verified repair trajectories with tests**, not simply more raw code. For Mikoo's 354M model and 749 MB RAM target, a smaller high-quality dataset with compiler/test feedback, repository context, multilingual prompts, and strict tool honesty should outperform a much larger noisy corpus for the intended agent tasks. Train the model to produce a safe, reviewable, test-aware patch—and to admit when it cannot verify the result.

## References

[1]: https://github.com/github/CodeSearchNet "GitHub CodeSearchNet repository"

[2]: https://huggingface.co/datasets/nvidia/OpenCodeInstruct "NVIDIA OpenCodeInstruct dataset card"

[3]: https://www.bigcode-project.org/docs/about/the-stack/ "BigCode The Stack data governance"

[4]: https://www.swebench.com/SWE-bench/ "SWE-bench overview"

[5]: https://www.swebench.com/verified.html "SWE-bench Verified"
