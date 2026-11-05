"""Exercise the CLI against real local Git repositories, without network access."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_dependencies.py"


class DependencyChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "hvco"
        (self.project / "scripts").mkdir(parents=True)
        self.script = self.project / "scripts" / SCRIPT.name
        shutil.copyfile(SCRIPT, self.script)
        self.checkout = self.root / "source"
        self.checkout.mkdir()
        self.git("init", "-q")
        (self.checkout / "contract.md").write_text("contract\n", encoding="utf-8")
        (self.checkout / ".gitignore").write_text("runs/\n", encoding="utf-8")
        self.git("add", ".")
        self.commit()
        self.item = {"name": "source", "url": "https://example.org/source.git",
                     "revision": self.git("rev-parse", "HEAD").strip(),
                     "files": ["contract.md"], "purpose": "Contract fixture"}
        self.write_manifest()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.checkout), *args],
                                       stderr=subprocess.DEVNULL, text=True)

    def commit(self):
        self.git("-c", "user.name=Dependency Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")

    def write_manifest(self):
        (self.project / "dependencies.json").write_text(
            json.dumps({"dependencies": [self.item]}), encoding="utf-8")

    def run_check(self, *args):
        return subprocess.run([sys.executable, str(self.script), *map(str, args)],
                              cwd=self.root.parent, capture_output=True, text=True)

    def test_default_root_is_project_parent_and_ignored_runs_are_clean(self):
        (self.checkout / "runs").mkdir()
        (self.checkout / "runs" / "draft.md").write_text("draft", encoding="utf-8")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(str(self.checkout) + ": ok", result.stdout)
        self.assertEqual(self.run_check("--root", self.root).returncode, 0)
        self.assertEqual(self.run_check("--root", self.project).returncode, 1)

    def test_missing_checkout_stale_pin_and_missing_file(self):
        moved = self.root / "moved"
        self.checkout.rename(moved)
        self.assertIn("missing checkout", self.run_check().stdout)
        self.assertEqual(self.run_check().returncode, 1)
        moved.rename(self.checkout)
        (self.checkout / "contract.md").write_text("new contract", encoding="utf-8")
        self.git("add", ".")
        self.commit()
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale revision", result.stdout)
        self.item["revision"] = self.git("rev-parse", "HEAD").strip()
        self.item["files"] = ["absent.md"]
        self.write_manifest()
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing/invalid required file", result.stdout)

    def test_tracked_and_untracked_changes_fail_without_mutation(self):
        tracked = self.checkout / "contract.md"
        tracked.write_text("edited", encoding="utf-8")
        self.git("add", "contract.md")
        before = self.git("status", "--porcelain=v1")
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("dirty checkout", result.stdout)
        self.assertEqual(before, self.git("status", "--porcelain=v1"))
        self.git("reset", "--hard", "-q", "HEAD")
        (self.checkout / "untracked.md").write_text("new", encoding="utf-8")
        self.assertEqual(self.run_check().returncode, 1)
        self.assertIn("dirty checkout", self.run_check().stdout)

    def test_manifest_rejects_escaping_paths_and_nonexact_pins(self):
        for field, value in [("files", ["../outside.md"]), ("files", ["/tmp/file"]),
                             ("files", ["a/./b"]), ("name", "../source"),
                             ("revision", "HEAD"), ("revision", "a" * 39)]:
            with self.subTest(field=field, value=value):
                original = self.item[field]
                self.item[field] = value
                self.write_manifest()
                result = self.run_check()
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid manifest", result.stderr)
                self.assertEqual(result.stdout, "")
                self.item[field] = original


if __name__ == "__main__":
    unittest.main()
