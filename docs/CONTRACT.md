# Contract format (schema_version = 1)

`experiment.json` is UTF-8 JSON. Unknown keys are rejected so a misspelled budget cannot silently disappear.

```json
{
  "schema_version": 1,
  "title": "Reviewed baseline check",
  "stage": "baseline-validation",
  "command": ["{python}", "src/baseline.py", "--seed", "42"],
  "files": ["src/baseline.py", "src/helper.py", "data/validation.csv"],
  "outputs": ["metrics.json"],
  "timeout_seconds": 60,
  "max_log_bytes": 65536,
  "max_runs": 2,
  "metric": {"file": "metrics.json", "name": "mae", "direction": "min", "baseline": 2.0}
}
```

This is a format example, not included research data or an implemented baseline.

| Field | Meaning |
| --- | --- |
| `title`, `stage` | Nonempty text, at most 200 characters each |
| `command` | Argument array beginning with `{python}` and a listed `.py` file; no shell interpolation |
| `files` | 1–500 exact source/input files copied to the working snapshot. Include local imports and configuration files. Directories/globs are unsupported. |
| `outputs` | 1–500 expected regular files under the working snapshot; never overlap inputs |
| `timeout_seconds` | Integer 1–3600; wall-clock budget, polled about every 10 ms plus cleanup overhead |
| `max_log_bytes` | Integer 1024–1048576; maximum stored bytes of combined stdout/stderr. Exceeding it requires review. |
| `max_runs` | Integer 1–100 per approval; interrupted and failed runs are recorded. Any failure blocks subsequent runs pending reapproval. |
| `metric` | One JSON output object containing a finite number under `name`. `min` passes when value ≤ baseline, `max` when value ≥ baseline. Equality passes. |

Paths use relative forward slashes, with no traversal, symlink, junction, drive prefix, Windows device names, case-only duplicates, or overlapping input/output paths. Script arguments are literal strings; script behavior remains the teacher's responsibility.

Project ancestors must also be real directories. On macOS, paths below `/var` or `/tmp` may use system symlinks; use the canonical path (for example `/private/var/...`) or create the project under your home directory. The test fixture resolves its temporary parent before creating a project.

The teacher supplies a meaningful baseline threshold. The runner does not compute an independent baseline or verify that the script calculated its metric honestly. Save additional metrics/plots as declared output files, but only the selected metric controls the v0.1.0 gate.

## Approval and state

`approve` writes `.modeling_guard/approval.json` with a reviewer label, UTC time, unique approval ID, normalized contract SHA-256, and SHA-256 for every declared input file. Reapproving creates a new ID and resets the run allowance; old runs remain for inspection. Normalizing the JSON permits harmless whitespace changes.

`run` checks the approval, acquires an exclusive lock, checks earlier runs, creates a run receipt **before** executing, copies only the declared files, hashes the copy again, and launches one Python process. The working directory is the new `work/` snapshot, so relative reads/writes use that snapshot. Ordinary edits to project files do not silently change an approved run.

`STOP` (exit code 2) means a preflight failure and the command did not start. `REVIEW_REQUIRED` (exit code 2) means an allocated run failed or was interrupted; inspect its report. `PASS` (exit code 0) means the declared checks passed. CLI argument errors also exit 2 with usage text.

The runner records the Python version and OS family, not a full dependency lock, container image, external resources, randomness, hardware, or network responses. Reproduction still requires those dependencies to be managed separately. No reproducibility guarantee is made for undeclared resources.

## Recovery

If the host crashes, an unfinished run remains non-PASS and blocks retry. If `active.lock` remains, first verify that no corresponding runner/child process is active, then remove **only that stale lock**. Inspect the unfinished run before the teacher reapproves. Never erase history simply to obtain a green result.
