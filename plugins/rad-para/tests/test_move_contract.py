import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "para_move.py"
SPEC = importlib.util.spec_from_file_location("para_move", SCRIPT)
MOVE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOVE)


class MoveContractTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "para"
        for folder in ("Projects", "Areas", "Resources", "Archives"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.ledger = self.root / "move-ledger.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def add_file(self, relative, content="x"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def plan(self, pairs):
        return MOVE.write_dry_run_ledger(self.root, pairs, self.ledger)

    def test_successful_dry_run_and_apply(self):
        source = self.add_file("Projects/note.md")
        target = self.root / "Resources" / "note.md"
        value = self.plan([("Projects/note.md", "Resources/note.md")])
        self.assertFalse(target.exists())
        self.assertFalse(value["approved"])

        MOVE.approve_ledger(self.ledger, self.root)
        result = MOVE.apply_ledger(self.ledger, root=self.root)

        self.assertFalse(source.exists())
        self.assertTrue(target.exists())
        self.assertEqual(result["status"], "applied")
        self.assertTrue(self.ledger.exists())

    def test_unapproved_apply_is_rejected(self):
        self.add_file("Projects/note.md")
        self.plan([("Projects/note.md", "Resources/note.md")])

        with self.assertRaises(MOVE.MoveContractError):
            MOVE.apply_ledger(self.ledger, root=self.root)

    def test_ledger_boundary_is_checked_before_reading(self):
        outside = Path(self.tempdir.name) / "outside-ledger.json"
        outside.write_text("{}", encoding="utf-8")
        with mock.patch.object(MOVE.Path, "read_text", side_effect=AssertionError("read happened")):
            with self.assertRaisesRegex(MOVE.MoveContractError, "escapes"):
                MOVE.load_ledger(outside, self.root)

    def test_python_api_has_no_approval_bypass(self):
        self.add_file("Projects/note.md")
        self.plan([("Projects/note.md", "Resources/note.md")])
        with self.assertRaises(TypeError):
            MOVE.apply_ledger(self.ledger, root=self.root, approved=True)

    def test_in_memory_mapping_is_rejected(self):
        with self.assertRaisesRegex(MOVE.MoveContractError, "durable ledger path"):
            MOVE.apply_ledger({"approved": True, "status": "approved", "entries": []}, root=self.root)

    def test_target_escape_is_rejected(self):
        self.add_file("Projects/note.md")
        with self.assertRaisesRegex(MOVE.MoveContractError, "escapes"):
            self.plan([("Projects/note.md", "../outside.md")])

    def test_collision_is_rejected(self):
        self.add_file("Projects/note.md")
        self.add_file("Resources/note.md")
        with self.assertRaisesRegex(MOVE.MoveContractError, "already exists"):
            self.plan([("Projects/note.md", "Resources/note.md")])

    def test_link_is_rejected(self):
        source = self.root / "Projects" / "linked.md"
        outside = Path(self.tempdir.name) / "outside.md"
        outside.write_text("x", encoding="utf-8")
        try:
            source.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("file symlinks are unavailable")

        with self.assertRaisesRegex(MOVE.MoveContractError, "link"):
            self.plan([("Projects/linked.md", "Resources/linked.md")])

    def test_failure_after_one_move_restores_prior_paths_and_keeps_ledger(self):
        source_one = self.add_file("Projects/one.md", "one")
        source_two = self.add_file("Projects/two.md", "two")
        target_one = self.root / "Resources" / "one.md"
        target_two = self.root / "Resources" / "two.md"
        self.plan(
            [
                ("Projects/one.md", "Resources/one.md"),
                ("Projects/two.md", "Resources/two.md"),
            ]
        )

        calls = []

        def fail_second(source, target):
            calls.append((source, target))
            if len(calls) == 2:
                raise OSError("injected failure")
            return shutil.move(source, target)

        MOVE.approve_ledger(self.ledger, self.root)
        with self.assertRaises(MOVE.MoveApplyError):
            MOVE.apply_ledger(self.ledger, root=self.root, move_fn=fail_second)

        self.assertTrue(source_one.exists())
        self.assertFalse(target_one.exists())
        self.assertTrue(source_two.exists())
        self.assertFalse(target_two.exists())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(ledger["status"], "failed_restored")
        self.assertEqual(ledger["entries"][0]["status"], "restored")
        self.assertEqual(ledger["entries"][1]["status"], "failed")

    def test_incomplete_restoration_keeps_exact_paths(self):
        source_one = self.add_file("Projects/one.md", "one")
        self.add_file("Projects/two.md", "two")
        self.plan(
            [
                ("Projects/one.md", "Resources/one.md"),
                ("Projects/two.md", "Resources/two.md"),
            ]
        )

        calls = []

        def fail_second(source, target):
            calls.append((source, target))
            if len(calls) == 2:
                raise OSError("injected apply failure")
            return shutil.move(source, target)

        def fail_restore(source, target):
            raise OSError("injected restoration failure")

        MOVE.approve_ledger(self.ledger, self.root)
        with self.assertRaises(MOVE.MoveApplyError):
            MOVE.apply_ledger(
                self.ledger,
                root=self.root,
                move_fn=fail_second,
                restore_fn=fail_restore,
            )

        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(ledger["status"], "restoration_incomplete")
        self.assertTrue(ledger["restoration_errors"])
        self.assertEqual(ledger["entries"][0]["source"], str(source_one.resolve()))
        self.assertEqual(ledger["entries"][0]["target"], str((self.root / "Resources" / "one.md").resolve()))

    def test_permission_error_is_rejected_before_apply(self):
        source = self.add_file("Projects/note.md")
        with mock.patch.object(MOVE.Path, "lstat", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(MOVE.MoveContractError, "cannot inspect"):
                MOVE.validate_moves(self.root, [(source, self.root / "Resources" / "note.md")])

    def test_ledger_write_failure_after_move_restores_and_keeps_evidence(self):
        source = self.add_file("Projects/write-failure.md", "x")
        self.plan([("Projects/write-failure.md", "Resources/write-failure.md")])
        MOVE.approve_ledger(self.ledger, self.root)
        original_write = MOVE._write_json
        calls = []

        def fail_after_move(path, value):
            calls.append(value.get("status"))
            if len(calls) == 2:
                raise OSError("injected ledger write failure")
            return original_write(path, value)

        with mock.patch.object(MOVE, "_write_json", fail_after_move):
            with self.assertRaises(MOVE.MoveApplyError) as raised:
                MOVE.apply_ledger(self.ledger, root=self.root)

        self.assertTrue(source.exists())
        self.assertFalse((self.root / "Resources" / "write-failure.md").exists())
        self.assertIn("ledger write", str(raised.exception.result["apply_error"]).lower())
        ledger = json.loads(self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(ledger["status"], "failed_restored")
        self.assertEqual(ledger["entries"][0]["status"], "restored")

    def test_cli_dry_run_approve_apply(self):
        source = self.add_file("Projects/cli.md", "cli")
        target = self.root / "Resources" / "cli.md"
        command = [sys.executable, str(SCRIPT)]
        dry_run = subprocess.run(
            command
            + [
                "--root",
                str(self.root),
                "--move",
                "Projects/cli.md",
                "Resources/cli.md",
                "--dry-run",
                "--ledger",
                str(self.ledger),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        approve = subprocess.run(
            command + ["--root", str(self.root), "--ledger", str(self.ledger), "--approve"],
            capture_output=True,
            text=True,
            check=False,
        )
        apply = subprocess.run(
            command + ["--root", str(self.root), "--ledger", str(self.ledger), "--apply"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertEqual(approve.returncode, 0, approve.stderr)
        self.assertEqual(apply.returncode, 0, apply.stderr)
        self.assertFalse(source.exists())
        self.assertTrue(target.exists())

    def test_linked_target_parent_is_rejected(self):
        source = self.add_file("Projects/note.md")
        link_parent = self.root / "linked-resources"
        try:
            link_parent.symlink_to(self.root / "Resources", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks are unavailable")

        with self.assertRaisesRegex(MOVE.MoveContractError, "link"):
            self.plan([(source, link_parent / "note.md")])


if __name__ == "__main__":
    unittest.main()
