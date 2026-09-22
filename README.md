# Modeling Guard

**Teacher-approved experiments. Bounded runs. Inspectable evidence.**

[中文说明](README.zh-CN.md) · [60-second demo](docs/DEMO.md) · [Contract reference](docs/CONTRACT.md) · [Limitations](SECURITY.md) · [Contribute](CONTRIBUTING.md)

An offline Python tool for teachers and students working with AI-assisted modeling code. Review one experiment stage, bind approval to the exact declared code and data, run within a time/log/attempt budget, and open a self-contained HTML receipt.

**No API key, GitHub account, Git, third-party Python runtime dependency, or AI subscription is needed for the core tool. Python 3.10+ is required.** There are no model calls or telemetry. Source ZIP use requires no package installation.

```text
Teacher reviews        Approval binds          Student runs         Teacher inspects
contract + files   →   SHA-256 fingerprints →   one bounded stage →  HTML + JSON + logs
                             ↑                       │
                     reapproval required ← failure / change / exhausted budget
```

## Try the synthetic demo

Download this repository using **Code → Download ZIP**, extract it, and open a terminal in the extracted folder. No GitHub login is needed to download a public repository.

```sh
python -m modeling_guard init demo-project
python -m modeling_guard check demo-project
# Read demo-project/experiment.json and experiment.py before approving.
python -m modeling_guard approve demo-project --teacher "Demo reviewer"
python -m modeling_guard run demo-project
```

On Windows, `py -3` can replace `python`. You can also double-click **RUN_DEMO.cmd** for a clearly labeled synthetic demonstration; it approves only the bundled demo, creates a fresh folder, and opens the report. It does not approve student work.

Expected: `PASS`, measured MAE `1.0`, threshold `≤ 2.0`, plus the path to `report.html`. The five reference/prediction pairs are deliberately synthetic software test data. **No model is fitted and no contest problem is solved.** Runtime varies by machine.

The output lives in `demo-project/.modeling_guard/runs/<run-id>/`:

| File | Purpose |
| --- | --- |
| `report.html` | Standalone bilingual receipt; no server or external assets |
| `result.json`, `contract.json` | Status, command arguments, threshold, Python/OS version, and file hashes |
| `console.log` | Bounded combined stdout/stderr |
| `work/` | Snapshot of declared source/data files and experiment outputs |
| `STAGE_REPORT.md` | One-stage summary |
| `HUMAN_REVIEW.md` | Created when a run needs review |

## What happens when something changes?

| Trigger | Behavior |
| --- | --- |
| No approval, changed code/data/contract | `STOP`; command never starts |
| Timeout, excessive logs, nonzero exit | `REVIEW_REQUIRED`; ordinary running process tree is stopped on timeout |
| Missing output, non-finite metric, missed baseline threshold | `REVIEW_REQUIRED`; automatic retry is blocked |
| Input modified inside the work snapshot | `REVIEW_REQUIRED`; original project inputs are not the working copy |
| Attempt budget used up | `STOP`; a new teacher review is required |
| All declared checks pass | `PASS`; teacher still interprets the result |

Approval is a **local workflow record, not authenticated identity or a security sandbox**. A user or agent with filesystem access can edit it or bypass the tool. Only run code you trust. Windows child cleanup has limitations; see [SECURITY.md](SECURITY.md). Thresholds and emitted metrics are not independently validated scientific evidence.

## Use it with your own experiment

1. Create a fresh project with `init`, then replace the synthetic files with your own reviewed files.
2. Edit `experiment.json`: one Python script with explicit arguments, all imported local source files/data, expected outputs, metric threshold, and budgets. See [the full contract](docs/CONTRACT.md).
3. Run `check`; have the teacher review both the contract and code. Run `approve --teacher "NAME"` only after that review.
4. Run one stage, inspect the report, and stop before changing the modeling route. A failure requires reapproval even if attempts remain.

The runner uses the same Python interpreter it was started with. Install scientific packages in your own project virtual environment as needed. The tool does not download dependencies, hash external packages, track undeclared data, block network access, measure token spending, or enforce CPU/RAM/GPU quotas. There is a wall-clock limit, stored log limit, and run-count limit.

## AI assistant and student distribution

The core CLI can be called manually or from any assistant with terminal access. A web-only chat cannot execute it on a student's computer. `init` includes short cooperative `AGENTS.md` instructions; per-assistant discovery is not assumed. See [integration notes](docs/INTEGRATIONS.md).

The optional [Codex student installer](extras/codex-student-pack/README_学生安装.md) preserves an earlier fixed-commit download workflow. It requires Git and network access, downloads third-party code from its original repository, and is **not required by Modeling Guard**. The original repository's redistribution license is unclear and some subtools contain proprietary terms. No upstream source is bundled. Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before opting into it.

“Low token” means setup/checks do not invoke a model and the handoff is short. It is not a measured percentage reduction in AI usage.

## Development

```sh
python -m unittest discover -s tests -v
python scripts/build_zip.py
```

Optional installation from source: `python -m pip install .` (the build may fetch setuptools; the runtime has no dependencies). Then use `modeling-guard` as the CLI command. No PyPI publication is claimed.

GitHub Actions is configured for Windows, Linux and macOS on Python 3.10/3.12. A configured matrix is not evidence that CI has run: check the repository's actual Actions results. The local acceptance record is in [docs/VALIDATION.md](docs/VALIDATION.md).

## Project status

v0.1.0 is an early teaching-workflow tool. Community adoption, cross-tool integrations, scientific validation, and authenticated remote approvals are not established. We welcome real classroom feedback, reproducible bugs, tests, and small changes that make experiment evidence easier to inspect.

This is an independent project, not an official OpenAI product and not endorsed by OpenAI. Development was assisted by Codex; generated contributions need the same human review as other code.

MIT license for the original files in this repository. External software retains its own terms.
