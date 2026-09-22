# Contributing

Useful contributions start with a real reproducible problem: an installation failure, an ambiguous teacher contract, a misleading report, or a boundary case in run handling. Use synthetic data in issues and tests.

1. Open an issue explaining the trigger, expected behavior, observed output, OS, and Python version. Redact private paths and data.
2. Keep each change small. Run `python -m unittest discover -s tests -v` from the repository root.
3. Include a regression test for execution, approval, path, or metric behavior. Documentation-only edits do not need artificial tests.
4. Update both README languages when changing user-facing setup or capability claims.
5. Do not add telemetry, API dependencies, global configuration edits, or silent overwrites as convenience features.

AI-assisted contributions are welcome. Review the code, verify behavior, explain limitations, and cite external source material. Do not paste third-party code whose license is unclear. Contributions are under this repository's MIT license.

No adoption metric, testimonial, benchmark, or compatibility badge should be added without checkable evidence. Prioritize real usefulness over stars.
