# Acceptance record

Date: 2026-09-22. Release candidate: 0.1.0.

## Executed locally

- Windows, Python 3.12.14.
- `python -W error::ResourceWarning -m unittest discover -s tests -v`: **25 tests passed, 0 failures, 0 skips** after closing a log-reader handle exposed during the first test run.
- Actual `RUN_DEMO.cmd -NoOpen -NoPause`: **DEMO_OK**, status PASS, measured synthetic MAE 1.0, threshold 2.0. No model fitting or external service.
- Opened the actual generated HTML report in a browser and inspected the desktop layout, bilingual text, status, metric, threshold, runtime and provenance fields.
- Built a source ZIP; extracted into a fresh directory and ran its Windows demo launcher successfully.
- Built a Python wheel; installed it with `--no-index --no-deps` into a fresh virtual environment and ran the bundled demo successfully from outside the source tree.
- Checked local Markdown links and the ZIP's public-content allowlist. No upstream checkout, approval records, private run directories, or account credentials were bundled.

Tests cover unapproved/stale approval refusal, no-overwrite initialization, input snapshot preservation, failed-run retry blocking, run budget, timeout, normal child-process cleanup, bounded logs, output/metric failures, malformed contract/receipt, path restrictions, concurrent-operation lock, HTML escaping, and exclusion of an inherited test secret from the child environment.

## Not established by these checks

- macOS/Linux execution until the configured CI jobs actually pass.
- Scientific correctness, absence of information leakage, full environment reproducibility, token savings, or improved competition performance.
- Authenticated teacher identity, hostile-code isolation, detached-process containment, CPU/RAM/GPU or financial quotas.
- Live product-specific acceptance of the new runner in Codex, Cursor, Claude Code or other assistants.
- Community adoption, classroom deployment numbers, or any external program selection.

The optional older Skill installer had separate teacher-side acceptance before this project was created. Its original local logs and upstream checkout are not public release artifacts; do not interpret that prior result as validation of all future upstream behavior.
