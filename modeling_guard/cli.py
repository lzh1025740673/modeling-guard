"""Small CLI that works from a downloaded ZIP without installing a package."""

import argparse
from importlib.resources import files
from pathlib import Path
import sys

from . import __version__
from .core import GuardError, approve, contract_for, fingerprint, reject_links, run


def init(project):
    target = Path(project).absolute()
    reject_links(target)
    if target.exists():
        raise GuardError("init requires a new directory; existing files are never overwritten")
    source = files("modeling_guard").joinpath("demo")
    target.mkdir(parents=True)
    for name in ("experiment.json", "experiment.py", "data.csv", "AGENTS.md"):
        with (target / name).open("xb") as stream:
            stream.write(source.joinpath(name).read_bytes())
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description="Modeling Guard: approve, run, and inspect one bounded experiment stage.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("init", "check", "approve", "run"):
        cmd = sub.add_parser(name)
        cmd.add_argument("project", type=Path)
        if name == "approve":
            cmd.add_argument("--teacher", required=True, help="Reviewer label; not authenticated identity")
    args = parser.parse_args(argv)
    try:
        if args.action == "init":
            path = init(args.project)
            print(f"INITIALIZED: {path}\nRead experiment.json and experiment.py, then have a teacher approve. No experiment has run.")
        elif args.action == "check":
            spec = contract_for(args.project)
            hashes = fingerprint(args.project, spec)
            print(f"CONTRACT_VALID: {spec['stage']} / {len(hashes)} files / {spec['timeout_seconds']} s / {spec['max_runs']} runs\nThis validates the contract; it does not approve or execute it.")
        elif args.action == "approve":
            receipt = approve(args.project, args.teacher)
            print("APPROVED: " + receipt["approval_id"] + "\nThis local receipt binds the contract and listed file contents; it does not authenticate the reviewer.")
        elif args.action == "run":
            folder, result = run(args.project)
            print(result["status"] + ": " + result["reason"] + "\nREPORT: " + str(folder / "report.html"))
            return 0 if result["status"] == "PASS" else 2
        return 0
    except (GuardError, OSError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2
