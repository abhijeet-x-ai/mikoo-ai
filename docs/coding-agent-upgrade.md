# Mikoo AI Coding Agent Upgrade Report

## Executive result

Mikoo AI has been upgraded in design and project structure from a general offline chat assistant to a **focused offline coding agent**. The new target covers code completion, code explanation, unit-test generation, debugging, bug fixing, refactoring, code translation, repository-context retrieval, patch proposal, and safe structured tool use.

The model remains subject to the existing hardware contract: a hard **749 MB peak application-RAM ceiling**, an operational target of **650 MB or less**, and a smooth default profile for 2 GB RAM Android phones. The preferred profile is INT4-group quantization, 512-token context, one inference worker, batch size one, and a 768 byte-token default generation cap with a 1,024-unit native ceiling.

## Capability boundary

The mobile agent can generate and explain code, inspect user-selected files through bounded context, propose minimal diffs, generate tests, interpret compiler/test logs, and summarize risks. Applying a patch requires explicit approval. Running tests or builds requires an allowlisted command profile, timeout, bounded output, and explicit approval. Arbitrary shell commands, network access, package installation, secret access, destructive operations, and silent file modification are not allowed.

Repository-wide autonomous issue resolution, repeated test/refine loops, and full SWE-bench-style execution are external desktop/sandbox capabilities, not unrestricted default behavior on a 2 GB phone. This boundary is intentional: the model should be useful and safe rather than claim that a small mobile model is equivalent to a frontier coding system.

## Coding specialization

The training configuration now includes code and task coverage for Python, JavaScript/TypeScript, Kotlin/Java, C++, SQL, HTML/CSS, Bash, JSON, and YAML. Task mixtures cover completion, explanation, test generation, bug fixing, refactoring, error diagnosis, code translation, repository context, documentation, security review, and tool use.

The data format requires provenance, license, source, repository/path, checksum, split, and opt-out status. CodeSearchNet provides useful code/docstring and code-retrieval examples across several languages, but source-code licensing remains separate from the repository's MIT license [1]. BigCode's governance guidance reinforces provenance, original-license compliance including attribution, and a removal/opt-out process [2].

## Training strategy

The correct training sequence is code-language pretraining, instruction tuning, tool-action tuning, execution/refinement trajectory training, distillation, and quantization. Teacher-generated answers may be used only during training. The teacher is never shipped in the APK and is never required during offline inference.

Training examples should include both successful and failed attempts: compiler errors, failing tests, patch conflicts, corrections, minimal diffs, and final summaries. The student should learn not to claim that a tool succeeded without a tool result. Hidden chain-of-thought is not required; concise plans, structured actions, observable tool results, and final explanations are sufficient for the product.

Training the 354M production model from scratch or distilling it requires a separate GPU-capable environment. The current sandbox has 6 CPU cores, approximately 3.8 GiB RAM, 2 GiB swap, and no CUDA GPU. It can train the self-authored bootstrap checkpoint and run pipeline smoke tests, but not a useful high-data production run. The repository includes the model trainer, data cleaner, license/provenance gates, code-record schema, training configuration, prompt templates, tool schema, and evaluation harness needed for the next training machine.

## Evaluation plan

A coding model must not be evaluated only on short function generation. Mikoo's evaluation includes syntax and compile checks, unit-test generation, seeded bug repair, patch minimality, code explanation, code translation, tool-schema validity, bounded repository context selection, cancellation, and memory behavior. Repository-level evaluation should apply patches and run tests, matching the core principle of SWE-bench-style evaluation [3]. SWE-bench Verified is a human-validated subset of 500 instances, but its full environment is not suitable for direct default execution on a 2 GB phone [4].

| Evaluation family | Pass signal |
|---|---|
| Completion | Code parses/compiles and satisfies hidden tests |
| Explanation | Human or rubric score for correctness and completeness |
| Unit tests | Tests run and detect seeded defects without excessive brittleness |
| Bug fixing | Patch applies cleanly and relevant tests pass |
| Refactoring | Behavior-preserving tests pass and diff stays scoped |
| Repository context | Relevant files selected within the context budget |
| Tool use | JSON schema valid; writes/execution require approval; no fabricated success |
| Refinement | Test feedback leads to a better patch without regression |
| Mobile | Offline operation, bounded memory, stable latency, no frequent crashes/ANRs |

## Implemented project artifacts

The repository now includes `docs/coding-agent-spec.md`, `docs/coding-training-plan.md`, `model/coding_agent_tools.schema.json`, `model/coding_prompt_templates.md`, `training/code_record.schema.json`, coding-agent configuration sections, `benchmarks/coding_eval.py`, `android/.../WorkspacePolicy.kt`, `android/.../CodingAgentContract.kt`, an offline workspace picker, and expanded validation tests.

The native C++ bridge now loads the bundled self-authored bootstrap checkpoint and performs bounded offline neural generation. The planned 354M production runtime remains guarded until its larger checkpoint, tokenizer, quantization, and validation are complete. The app does not claim that a patch or test operation happened without an observable local tool result.

## Honest status

The system now includes a real local neural bootstrap coding model and an Android JNI inference path, but it is not yet a trained “super coding agent.” The remaining production steps are high-volume license-audited data preparation, 24,576-token tokenizer training, GPU pretraining, instruction and agent-trajectory tuning, INT4 quantization, production runtime integration, and measurements on a real 2 GB Android phone. The bootstrap acceptance suite passes 5/5 cases; this is not a broad coding benchmark or a claim of production-model quality.

## References

[1]: https://github.com/github/CodeSearchNet "GitHub CodeSearchNet repository"

[2]: https://www.bigcode-project.org/docs/about/the-stack/ "BigCode The Stack data governance"

[3]: https://www.swebench.com/SWE-bench/ "SWE-bench overview"

[4]: https://www.swebench.com/verified.html "SWE-bench Verified"
