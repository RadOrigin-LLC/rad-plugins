from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit import PLUGIN_SCHEMA, audit_path
import convert as convert_module
from convert import create_plugin


class CreatePluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)

    def test_create_writes_portable_and_codex_manifests_with_optional_skill(self) -> None:
        target = self.base / "sample-plugin"

        result = create_plugin(
            target,
            name="sample-plugin",
            description="Check sample packages.",
            author="RAD",
            version="0.1.0",
            license_id="MIT",
            skill_name="check-sample",
            skill_description="Use when checking a sample package.",
        )

        portable = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((target / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        skill = (target / "skills" / "check-sample" / "SKILL.md").read_text(encoding="utf-8")

        self.assertTrue(result.successful, [item.to_dict() for item in result.findings])
        self.assertEqual(PLUGIN_SCHEMA, portable["$schema"])
        self.assertEqual("sample-plugin", portable["name"])
        self.assertNotIn("skills", portable)
        self.assertNotIn("interface", portable)
        self.assertEqual("./skills/", codex["skills"])
        self.assertEqual("Sample Plugin", codex["interface"]["displayName"])
        self.assertIn("name: check-sample", skill)
        self.assertTrue(audit_path(target).conforming)

    def test_create_refuses_nonempty_target_without_changing_it(self) -> None:
        target = self.base / "occupied"
        target.mkdir()
        sentinel = target / "keep.txt"
        sentinel.write_text("keep\n", encoding="utf-8")

        result = create_plugin(
            target,
            name="sample-plugin",
            description="Check sample packages.",
            author="RAD",
        )

        self.assertFalse(result.successful)
        self.assertEqual("keep\n", sentinel.read_text(encoding="utf-8"))
        self.assertIn("creation-target-not-empty", {item.code for item in result.findings})

    def test_create_requires_complete_optional_skill_metadata(self) -> None:
        target = self.base / "sample-plugin"

        result = create_plugin(
            target,
            name="sample-plugin",
            description="Check sample packages.",
            author="RAD",
            skill_name="check-sample",
        )

        self.assertFalse(result.successful)
        self.assertFalse(target.exists())
        self.assertIn("creation-skill-metadata", {item.code for item in result.findings})

    def test_create_dry_run_lists_writes_without_creating_target(self) -> None:
        target = self.base / "sample-plugin"

        result = create_plugin(
            target,
            name="sample-plugin",
            description="Check sample packages.",
            author="RAD",
            skill_name="check-sample",
            skill_description="Use when checking a sample package.",
            dry_run=True,
        )

        self.assertTrue(result.successful)
        self.assertTrue(result.dry_run)
        self.assertEqual(
            ["plugin.json", ".codex-plugin/plugin.json", "skills/check-sample/SKILL.md"],
            result.changed_files,
        )
        self.assertFalse(target.exists())

    def test_create_mid_write_failure_removes_transaction_files(self) -> None:
        target = self.base / "sample-plugin"
        original_write = convert_module._atomic_write_text

        def fail_codex_manifest(path: Path, text: str) -> bool:
            if path == target / ".codex-plugin" / "plugin.json":
                raise OSError("injected mid-write failure")
            return original_write(path, text)

        with mock.patch.object(convert_module, "_atomic_write_text", side_effect=fail_codex_manifest):
            result = create_plugin(
                target,
                name="sample-plugin",
                description="Check sample packages.",
                author="RAD",
                skill_name="check-sample",
                skill_description="Use when checking a sample package.",
            )

        self.assertFalse(result.successful)
        self.assertFalse(target.exists())
        self.assertIn("creation-transaction", {item.code for item in result.findings})


if __name__ == "__main__":
    unittest.main()
