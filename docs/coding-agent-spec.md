# Mikoo AI Coding Agent capability specification

## Product definition

Mikoo AI will be a **focused coding agent**, not a general-purpose autonomous software engineer. Its first target is an offline assistant that can understand bounded project context, generate and explain code, propose patches, debug small-to-medium problems, write tests, refactor files, and translate between natural-language requirements and implementation steps.

The 2 GB Android device is the primary inference target. The model will generate code locally, but unrestricted repository-wide autonomous execution is out of scope for the first mobile release because code execution, large repositories, build tools, and multi-step agent loops require more memory, time, and sandbox isolation than a phone should own.

## Capability tiers

| Tier | Capability | Mobile v1 status |
|---|---|---|
| 1 | Complete a function, explain code, generate a class/module, write comments and documentation | Required |
| 2 | Generate unit tests, test cases, type annotations, error handling, and API examples | Required |
| 3 | Diagnose compiler/test errors from pasted logs, propose a patch, refactor a bounded file, translate code between languages | Required |
| 4 | Inspect a user-selected project tree, retrieve relevant files, plan a change, emit a multi-file patch, and summarize risks | Controlled feature |
| 5 | Execute tests/builds, observe failures, revise the patch, and repeat | Desktop/explicit sandbox only; not unrestricted on-device execution |
| 6 | Autonomous repository-wide issue resolution with long trajectories and external tools | External evaluation/training profile, not the default 2 GB phone profile |

## Supported languages for the first coding model

The data and evaluation mix should prioritize Python, JavaScript/TypeScript, Kotlin, Java, C++, SQL, HTML/CSS, Bash, and JSON/YAML. Python and TypeScript should receive the strongest task coverage because they provide broad examples and fast local validation. Kotlin/Java and C++ are required for the Android ecosystem. Code data must be filtered for licenses, secrets, generated artifacts, malware, and low-quality duplication.

## Agent loop

The mobile assistant should use a bounded loop:

1. Parse the user's request and classify it as explain, generate, test, debug, refactor, translate, or patch.
2. Ask for or retrieve only the selected files and relevant context within a token budget.
3. Produce a short plan and a structured patch/tool proposal.
4. Allow the user to review and approve file changes.
5. Apply edits through a constrained patch engine.
6. If a user-approved sandbox is available, run only allowlisted tests or commands.
7. Feed bounded output logs back to the model for one or more repair attempts.
8. Show the final diff, test result, remaining uncertainty, and files changed.

The model must not silently modify files, execute arbitrary shell commands, access private data, exfiltrate files, install packages, or connect to the network. Tool calls must be structured and validated by the host application.

## Tool contract

The first tool set is deliberately small:

| Tool | Permission | Input bounds | Output bounds |
|---|---|---|---|
| `list_files` | User-selected workspace only | Max depth and file count | Paths only, no file contents |
| `read_file` | User-selected workspace only | Max bytes per file and total context | Truncated text with explicit marker |
| `search_files` | User-selected workspace only | Max matches and file types | Bounded snippets and paths |
| `propose_patch` | No write by default | Unified diff or structured edits | Diff preview |
| `apply_patch` | Explicit user approval | Changed files and byte limit | Applied files and checksum |
| `run_tests` | Explicit sandbox approval | Allowlisted command/profile, timeout, output cap | Exit code and bounded logs |
| `format_code` | Explicit approval or local-only formatter | Allowlisted language formatter | Diff and formatter result |

The agent must return a structured action object instead of inventing tool success. Every action records a request ID, workspace ID, input checksum, proposed files, approval state, output checksum, and error status.

## Safety boundaries

The code agent must treat repository files, comments, issue text, and logs as untrusted data. It should flag requests involving credential extraction, malware, persistence, unauthorized access, destructive commands, data exfiltration, or evasion. It should not run commands such as recursive deletion, disk formatting, credential harvesting, network scanning, or arbitrary downloads. Code execution must be opt-in, sandboxed, time-limited, resource-limited, and disconnected from sensitive device data.

## Quality definition

A high-quality result is not only code that looks plausible. The agent must preserve existing behavior where requested, produce syntactically valid code, explain assumptions, include tests where appropriate, show a minimal diff, identify unverified behavior, and report failed tests honestly. Repository-level success requires applying a patch and passing relevant tests, consistent with the evaluation logic used by SWE-bench-style benchmarks [1] [2].

## Reality check

A 354M-parameter model can become a strong small coding assistant after code-focused pretraining, instruction tuning, execution/refinement trajectories, and distillation, but it will not become equivalent to a frontier coding agent merely by adding a tool schema. The main capability gains must come from high-quality code data, compiler/test feedback, repository-context examples, and strict evaluation. The mobile model should therefore specialize rather than promise unrestricted autonomous software engineering.

## References

[1]: https://www.swebench.com/SWE-bench/ "SWE-bench overview"

[2]: https://www.swebench.com/verified.html "SWE-bench Verified"
