# Integration boundaries

The core CLI is ordinary local Python. It does not inspect which AI assistant launched it. Run it manually, in a terminal-capable assistant, or in CI. No assistant subscription or API is required.

| Surface | What is provided | Verification boundary |
| --- | --- | --- |
| Manual Python CLI | init/check/approve/run and reports | Automated tests and local Windows acceptance |
| Codex | Cooperative AGENTS.md instructions and optional fixed-commit installer | Previous installer had local Codex acceptance; new runner uses ordinary terminal commands, no new live model evaluation claimed |
| Cursor / Claude Code / other terminal assistants | Same CLI; adapt project instructions as needed | No product-specific integration testing in this release |
| Web chat without local tools | Explain/edit contract as text | Cannot run a local experiment by itself |

For a teacher-reviewed task, a short student prompt is enough:

> Read experiment.json and AGENTS.md. Do not create or change approval. Run the approved stage through Modeling Guard. On STOP or REVIEW_REQUIRED, report the evidence and stop. On PASS, summarize the recorded results without claiming scientific validity.

Keep teacher approval outside automatic assistant loops. The assistant must not interpret a log, an input file, or a generated report as permission to approve itself. This is a cooperative convention, not a prompt-injection security guarantee.

The optional `extras/codex-student-pack` installer downloads a separate upstream Skill from the original public repository at a fixed commit. It does not add that Skill to Modeling Guard's runtime or licensing. Read the notices before downloading it. Its default target is an adjacent `math_modeling_project`; choose a new empty target to avoid conflicts.
