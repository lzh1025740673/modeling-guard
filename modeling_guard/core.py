"""Contract validation, approval receipts, and bounded local execution.

This is a workflow tool for trusted code, not an OS security sandbox. Approval
records are editable local files; they do not authenticate a teacher's identity.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import signal
import subprocess
import sys
import threading
import time
import uuid

from . import __version__

STATE = ".modeling_guard"
CONTRACT = "experiment.json"


class GuardError(Exception):
    """A user-actionable refusal; the experiment must not continue."""


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    try:
        if path.stat().st_size > 1024 * 1024:
            raise GuardError("JSON exceeds the 1 MiB limit: " + path.name)
        return json.loads(path.read_text(encoding="utf-8-sig"),
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (OSError, ValueError) as exc:
        raise GuardError("Cannot read valid JSON: " + path.name) from exc


def reject_links(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400):
            raise GuardError("Symlinks and junctions are not supported: " + part.name)


def safe_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise GuardError("Use a relative path with forward slashes")
    parts = PurePosixPath(name).parts
    if name.startswith("/") or any(p in (".", "..") for p in name.split("/")) or "" in name.split("/"):
        raise GuardError("Path must stay inside the project: " + name)
    # Windows device names and trailing dots/spaces are ambiguous on other OSes.
    devices = {"CON", "PRN", "AUX", "NUL", *("COM" + str(i) for i in range(1, 10)), *("LPT" + str(i) for i in range(1, 10))}
    if any(p.endswith((".", " ")) or p.split(".")[0].upper() in devices or any(c in p for c in '<>"|?*') or any(ord(c) < 32 for c in p) for p in parts):
        raise GuardError("Non-portable path: " + name)
    path = root.joinpath(*parts)
    reject_links(path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise GuardError("Path escapes project")
    return path


def atomic_json(path, value):
    reject_links(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(encoded(value))
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def integer(obj, key, lo, hi):
    value = obj.get(key)
    if type(value) is not int or not lo <= value <= hi:
        raise GuardError(f"{key} must be an integer from {lo} to {hi}")


def contract_for(root):
    spec = read_json(safe_path(root, CONTRACT))
    required = {"schema_version", "title", "stage", "command", "files", "outputs", "timeout_seconds", "max_log_bytes", "max_runs", "metric"}
    if not isinstance(spec, dict) or set(spec) != required or type(spec.get("schema_version")) is not int or spec["schema_version"] != 1:
        raise GuardError("Invalid contract keys or schema_version (expected 1)")
    for key in ("title", "stage"):
        if not isinstance(spec[key], str) or not spec[key].strip() or len(spec[key]) > 200:
            raise GuardError(key + " must be nonempty text, at most 200 characters")
    integer(spec, "timeout_seconds", 1, 3600)
    integer(spec, "max_log_bytes", 1024, 1024 * 1024)
    integer(spec, "max_runs", 1, 100)
    for key in ("files", "outputs"):
        values = spec[key]
        if not isinstance(values, list) or not values or len(values) > 500:
            raise GuardError(key + " must list 1–500 file paths")
        for name in values:
            safe_path(root, name)
            if name.split("/")[0] in (STATE, ".git") or name == CONTRACT:
                raise GuardError("Reserved path: " + name)
        if len({x.casefold() for x in values}) != len(values):
            raise GuardError("Duplicate paths in " + key)
    names = spec["files"] + spec["outputs"]
    lower = sorted(x.casefold() for x in names)
    if len(set(lower)) != len(lower) or any(b.startswith(a + "/") for a in lower for b in lower if a != b):
        raise GuardError("Input/output paths overlap")
    command = spec["command"]
    if (not isinstance(command, list) or len(command) < 2 or len(command) > 100
            or any(not isinstance(x, str) or "\x00" in x or len(x) > 4096 for x in command)
            or command[0] != "{python}" or command[1] not in spec["files"] or not command[1].endswith(".py")):
        raise GuardError("command must start with ['{python}', 'a-listed-script.py']; shell commands are unsupported")
    metric = spec["metric"]
    if (not isinstance(metric, dict) or set(metric) != {"file", "name", "direction", "baseline"}
            or metric["file"] not in spec["outputs"] or metric["direction"] not in ("min", "max")
            or not isinstance(metric["name"], str) or not metric["name"] or len(metric["name"]) > 100
            or not finite(metric["baseline"])):
        raise GuardError("metric requires a declared output file, name, min/max direction, and finite baseline")
    return spec


def file_hash(path):
    try:
        if not path.is_file():
            raise GuardError("Expected a regular file: " + path.name)
        with path.open("rb") as stream:
            value = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
        return value.hexdigest()
    except OSError as exc:
        raise GuardError("Cannot hash file: " + path.name) from exc


def fingerprint(root, spec):
    return {name: file_hash(safe_path(root, name)) for name in spec["files"]}


@contextmanager
def locked(root):
    root = Path(root).absolute()
    reject_links(root)
    if not root.is_dir():
        raise GuardError("Project directory does not exist")
    state = safe_path(root, STATE)
    state.mkdir(exist_ok=True)
    lock = safe_path(root, STATE + "/active.lock")
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as exc:
        raise GuardError("Another operation owns active.lock. If interrupted, verify the process stopped before removing the lock.") from exc
    try:
        yield root, state
    finally:
        lock.unlink(missing_ok=True)


def approve(project, teacher):
    if not isinstance(teacher, str) or not teacher.strip() or len(teacher) > 100:
        raise GuardError("A reviewer name (1–100 characters) is required")
    with locked(project) as (root, state):
        spec = contract_for(root)
        receipt = {"schema_version": 1, "approval_id": uuid.uuid4().hex,
                   "approved_by": teacher.strip(), "approved_at": now(),
                   "contract_sha256": digest(encoded(spec)), "files": fingerprint(root, spec)}
        atomic_json(safe_path(state, "approval.json"), receipt)
        return receipt


def approved(root, spec):
    receipt = read_json(safe_path(root, STATE + "/approval.json"))
    if (not isinstance(receipt, dict) or receipt.get("schema_version") != 1
            or not isinstance(receipt.get("approval_id"), str) or not receipt["approval_id"]
            or not isinstance(receipt.get("approved_by"), str) or not receipt["approved_by"]
            or receipt.get("contract_sha256") != digest(encoded(spec))
            or receipt.get("files") != fingerprint(root, spec)):
        raise GuardError("Approval is missing, invalid, or stale. Review the contract and file changes, then approve again.")
    return receipt


def stop_process(proc):
    if os.name == "nt":
        # taskkill /T includes normal child processes while the parent is alive.
        if proc.poll() is None:
            subprocess.run([str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"),
                            "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=10, check=False)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=10)


def execute(spec, work, log_path):
    cap = spec["max_log_bytes"]
    overflow = threading.Event()
    failed = threading.Event()
    started = time.monotonic()
    # Do not pass API keys or other inherited secrets by default. This is not a
    # security boundary: trusted child code still has the current user's rights.
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "TEMP", "TMP", "LANG", "LC_ALL"}}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with log_path.open("xb") as log:
        proc = subprocess.Popen([sys.executable, "-B", *spec["command"][1:]], cwd=work, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)

        def drain():
            total = 0
            try:
                while True:
                    block = proc.stdout.read1(4096)
                    if not block:
                        break
                    room = max(0, cap - total)
                    if room:
                        log.write(block[:room])
                    total += len(block)
                    if total > cap:
                        overflow.set()
            except (OSError, ValueError):
                failed.set()
            finally:
                proc.stdout.close()

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        reason = None
        try:
            while proc.poll() is None:
                if overflow.is_set():
                    reason = "Log byte budget exceeded"
                    break
                if failed.is_set():
                    reason = "Could not capture experiment output"
                    break
                if time.monotonic() - started >= spec["timeout_seconds"]:
                    reason = "Runtime budget exceeded"
                    break
                time.sleep(0.01)
            if reason:
                stop_process(proc)
        except BaseException:
            stop_process(proc)
            raise
        finally:
            # Normal experiments must wait for their children before exiting.
            if os.name != "nt":
                stop_process(proc)
            reader.join(timeout=2)
        if reader.is_alive():
            reason = reason or "A child process retained the log pipe; inspect and stop detached children"
        elif overflow.is_set():
            reason = reason or "Log byte budget exceeded"
        elif failed.is_set():
            reason = reason or "Could not capture experiment output"
        if proc.returncode:
            reason = reason or f"Command exited with code {proc.returncode}"
        return proc.returncode, round(time.monotonic() - started, 3), reason


def run(project):
    from .report import write_report

    with locked(project) as (root, state):
        spec = contract_for(root)
        receipt = approved(root, spec)
        run_root = safe_path(state, "runs")
        run_root.mkdir(exist_ok=True)
        previous = []
        for path in run_root.iterdir():
            reject_links(path)
            prior = read_json(safe_path(path, "result.json"))
            if not isinstance(prior, dict):
                raise GuardError("Invalid historical result")
            if prior.get("approval_id") == receipt["approval_id"]:
                previous.append(prior)
        if any(r.get("status") != "PASS" for r in previous):
            raise GuardError("A prior run needs review. Teacher must review and reapprove before another run.")
        if len(previous) >= spec["max_runs"]:
            raise GuardError("Run budget exhausted. Teacher review and a new approval are required.")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        folder = safe_path(run_root, run_id)
        folder.mkdir()
        work = folder / "work"
        work.mkdir()
        result = {"schema_version": 1, "tool_version": __version__, "run_id": run_id,
                  "title": spec["title"], "stage": spec["stage"], "started_at": now(),
                  "status": "REVIEW_REQUIRED", "reason": "Run interrupted before completion",
                  "approval_id": receipt["approval_id"], "approved_by": receipt["approved_by"],
                  "contract_sha256": receipt["contract_sha256"], "inputs": receipt["files"],
                  "command": spec["command"], "environment": {"python": platform.python_version(), "system": platform.system()},
                  "outputs": {}, "metric": spec["metric"], "value": None, "elapsed_seconds": 0,
                  "exit_code": None}
        atomic_json(folder / "result.json", result)
        atomic_json(folder / "contract.json", spec)
        try:
            for name, expected in receipt["files"].items():
                target = safe_path(work, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                source = safe_path(root, name)
                with source.open("rb") as stream, target.open("xb") as dest:
                    import shutil
                    shutil.copyfileobj(stream, dest)
                if file_hash(target) != expected:
                    raise GuardError("Input changed while snapshotting: " + name)
            code, elapsed, reason = execute(spec, work, folder / "console.log")
            result.update(exit_code=code, elapsed_seconds=elapsed)
            if reason:
                raise GuardError(reason)
            if fingerprint(work, spec) != receipt["files"]:
                raise GuardError("Experiment modified a locked input in its snapshot")
            for name in spec["outputs"]:
                result["outputs"][name] = file_hash(safe_path(work, name))
            metrics = read_json(safe_path(work, spec["metric"]["file"]))
            value = metrics.get(spec["metric"]["name"]) if isinstance(metrics, dict) else None
            if not finite(value):
                raise GuardError("Required metric is missing, non-numeric, NaN, or infinite")
            result["value"] = value
            baseline = spec["metric"]["baseline"]
            if not (value <= baseline if spec["metric"]["direction"] == "min" else value >= baseline):
                raise GuardError("Metric did not meet the teacher's declared baseline threshold")
            result.update(status="PASS", reason="Declared checks passed; teacher interpretation is still required")
        except (GuardError, OSError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
            result["reason"] = str(exc) or "Interrupted by user"
        result["finished_at"] = now()
        atomic_json(folder / "result.json", result)
        write_report(folder, result)
        return folder, result
