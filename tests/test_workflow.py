import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from modeling_guard.cli import init
from modeling_guard.core import GuardError, STATE, approve, contract_for, encoded, run, safe_path
from modeling_guard.report import render


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="guard test 中文 ")
        self.addCleanup(self.temp.cleanup)
        # macOS exposes its temporary directory through /var -> /private/var.
        # Use the actual directory so the tests respect the no-symlink policy.
        self.project = init(Path(self.temp.name).resolve() / "new project")

    def edit_spec(self, **changes):
        path = self.project / "experiment.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        spec.update(changes)
        path.write_bytes(encoded(spec))

    def script(self, code):
        (self.project / "experiment.py").write_text(code, encoding="utf-8")

    def approved_run(self):
        approve(self.project, "Teacher test")
        return run(self.project)

    def test_init_never_overwrites(self):
        original = (self.project / "experiment.json").read_bytes()
        with self.assertRaises(GuardError):
            init(self.project)
        self.assertEqual((self.project / "experiment.json").read_bytes(), original)

    def test_check_does_not_approve(self):
        contract_for(self.project)
        self.assertFalse((self.project / STATE).exists())

    def test_unapproved_does_not_execute(self):
        self.script("raise RuntimeError('must not execute')")
        with self.assertRaises(GuardError):
            run(self.project)
        self.assertFalse((self.project / STATE / "runs").exists())

    def test_full_workflow_with_chinese_and_spaces(self):
        original = (self.project / "data.csv").read_bytes()
        folder, result = self.approved_run()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["value"], 1.0)
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue((folder / "report.html").is_file())
        self.assertIn("Synthetic acceptance fixture", (folder / "console.log").read_text(encoding="utf-8"))
        self.assertEqual((folder / "work" / "data.csv").read_bytes(), original)
        self.assertEqual((self.project / "data.csv").read_bytes(), original)
        self.assertNotIn(str(self.project), json.dumps(result))
        self.assertFalse((folder / "HUMAN_REVIEW.md").exists())

    def test_file_change_invalidates_approval(self):
        approve(self.project, "Teacher")
        with (self.project / "data.csv").open("a") as stream:
            stream.write("60,59\n")
        with self.assertRaisesRegex(GuardError, "stale"):
            run(self.project)

    def test_contract_change_invalidates_approval(self):
        approve(self.project, "Teacher")
        self.edit_spec(timeout_seconds=11)
        with self.assertRaisesRegex(GuardError, "stale"):
            run(self.project)

    def test_run_budget(self):
        self.edit_spec(max_runs=1)
        self.approved_run()
        with self.assertRaisesRegex(GuardError, "budget exhausted"):
            run(self.project)

    def test_failure_blocks_retry_until_reapproval(self):
        self.script("raise RuntimeError('intentional failure')")
        folder, result = self.approved_run()
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertTrue((folder / "HUMAN_REVIEW.md").is_file())
        with self.assertRaisesRegex(GuardError, "prior run"):
            run(self.project)

    def test_threshold_gate(self):
        self.edit_spec(metric={"file": "metrics.json", "name": "mae", "direction": "min", "baseline": 0.5})
        _, result = self.approved_run()
        self.assertEqual(result["value"], 1)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIn("baseline", result["reason"])

    def test_maximize_gate(self):
        self.edit_spec(metric={"file": "metrics.json", "name": "mae", "direction": "max", "baseline": 0.5})
        self.assertEqual(self.approved_run()[1]["status"], "PASS")

    def test_timeout(self):
        self.script("import time\nprint('started', flush=True)\ntime.sleep(30)")
        self.edit_spec(timeout_seconds=1)
        started = time.monotonic()
        _, result = self.approved_run()
        self.assertLess(time.monotonic() - started, 15)
        self.assertIn("Runtime budget", result["reason"])

    def test_log_limit(self):
        self.script("print('x' * 100000)")
        self.edit_spec(max_log_bytes=1024)
        folder, result = self.approved_run()
        self.assertLessEqual((folder / "console.log").stat().st_size, 1024)
        self.assertIn("Log byte budget", result["reason"])

    def test_missing_output(self):
        self.script("print('no output file')")
        _, result = self.approved_run()
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertIn("metrics.json", result["reason"])

    def test_invalid_metrics(self):
        for value in ("NaN", "Infinity", "true", '"1.0"', "null"):
            with self.subTest(value=value):
                self.script("from pathlib import Path\nPath('metrics.json').write_text(" + repr('{"mae":' + value + '}') + ")")
                _, result = self.approved_run()
                self.assertEqual(result["status"], "REVIEW_REQUIRED")

    def test_locked_input_mutation(self):
        self.script("from pathlib import Path\nPath('data.csv').write_text('changed')\nPath('metrics.json').write_text('{\"mae\":1}')")
        original = (self.project / "data.csv").read_bytes()
        _, result = self.approved_run()
        self.assertIn("modified a locked input", result["reason"])
        self.assertEqual((self.project / "data.csv").read_bytes(), original)

    def test_paths_reject_escape_and_windows_ambiguities(self):
        for path in ("../outside", "/absolute", "C:/file", "a\\b", "a/../b", "a//b", "NUL.txt", "a.", "foo\nbar"):
            with self.subTest(path=path), self.assertRaises(GuardError):
                safe_path(self.project, path)

    def test_duplicate_and_overlapping_paths(self):
        for paths in (["a", "a.txt", "a/b"], ["data.csv", "DATA.csv"]):
            with self.subTest(paths=paths):
                self.edit_spec(files=paths)
                with self.assertRaises(GuardError):
                    contract_for(self.project)

    def test_shell_command_rejected(self):
        self.edit_spec(command=["powershell", "-Command", "Get-Process"])
        with self.assertRaises(GuardError):
            contract_for(self.project)

    def test_invalid_budget_and_schema(self):
        for changes in ({"timeout_seconds": True}, {"schema_version": True}, {"max_runs": 0}, {"max_log_bytes": 1}, {"surprise": 5}):
            original = (self.project / "experiment.json").read_bytes()
            with self.subTest(changes=changes):
                self.edit_spec(**changes)
                with self.assertRaises(GuardError):
                    contract_for(self.project)
            (self.project / "experiment.json").write_bytes(original)

    def test_lock_prevents_concurrent_runs(self):
        approve(self.project, "Teacher")
        (self.project / STATE / "active.lock").write_text("123")
        with self.assertRaisesRegex(GuardError, "active.lock"):
            run(self.project)

    def test_corrupt_receipt_stops_without_execute(self):
        approve(self.project, "Teacher")
        (self.project / STATE / "approval.json").write_text("[]")
        with self.assertRaises(GuardError):
            run(self.project)

    def test_html_escapes_untrusted_labels(self):
        self.edit_spec(title='<script>alert("bad")</script>')
        _, result = self.approved_run()
        html = render(result)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn("default-src 'none'", html)

    def test_inherited_api_key_not_sent_to_experiment(self):
        original = os.environ.get("MODELING_GUARD_TEST_SECRET")
        os.environ["MODELING_GUARD_TEST_SECRET"] = "test-value-not-a-real-secret"
        try:
            self.script("import os\nfrom pathlib import Path\nassert 'MODELING_GUARD_TEST_SECRET' not in os.environ\nPath('metrics.json').write_text('{\"mae\":1}')")
            self.assertEqual(self.approved_run()[1]["status"], "PASS")
        finally:
            if original is None:
                del os.environ["MODELING_GUARD_TEST_SECRET"]
            else:
                os.environ["MODELING_GUARD_TEST_SECRET"] = original

    def test_timeout_stops_normal_child(self):
        marker = Path(self.temp.name) / "child-marker.txt"
        child = "import time; from pathlib import Path; time.sleep(3); Path(" + repr(str(marker)) + ").write_text('survived')"
        self.script("import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', " + repr(child) + "])\ntime.sleep(30)")
        self.edit_spec(timeout_seconds=1)
        self.assertIn("Runtime budget", self.approved_run()[1]["reason"])
        time.sleep(3)
        self.assertFalse(marker.exists())

    def test_cli_stop_exit_code(self):
        process = subprocess.run([sys.executable, "-m", "modeling_guard", "run", str(self.project)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        self.assertIn("STOP:", process.stderr)


if __name__ == "__main__":
    unittest.main()
