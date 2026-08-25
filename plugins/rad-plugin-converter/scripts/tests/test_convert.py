from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit import MCP_SCHEMA, PLUGIN_SCHEMA, audit_path
import convert as convert_module
from convert import convert_in_place, convert_marketplace, convert_to_target
from transaction import FileTransaction, TransactionError


class ConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.base = Path(self.temp_dir.name)

    def write_json(self, root: Path, relative: str, value: object) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return path

    def link_directory(self, target: Path, link: Path) -> None:
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")

    def write_skill(self, root: Path, directory: str = "check", name: str = "check") -> None:
        skill = root / "skills" / directory
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: Check plugins. Use when testing conversion.\n"
            "---\n\n"
            "# Check\n",
            encoding="utf-8",
        )

    def make_codex_plugin(self, name: str = "sample") -> Path:
        root = self.base / name
        root.mkdir()
        self.write_json(
            root,
            ".codex-plugin/plugin.json",
            {
                "name": name,
                "version": "2.3.4",
                "description": "Sample Codex plugin.",
                "author": {"name": "RAD"},
                "license": "MIT",
                "skills": "./skills/",
                "interface": {"displayName": "Sample"},
            },
        )
        self.write_skill(root)
        return root

    def test_codex_conversion_is_additive_and_repeatable(self) -> None:
        root = self.make_codex_plugin()
        compatibility_before = (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")

        first = convert_in_place(root)
        second = convert_in_place(root)
        portable = json.loads((root / "plugin.json").read_text(encoding="utf-8"))

        self.assertTrue(first.successful)
        self.assertEqual(["plugin.json"], first.changed_files)
        self.assertEqual([], second.changed_files)
        self.assertEqual(PLUGIN_SCHEMA, portable["$schema"])
        self.assertEqual("2.3.4", portable["version"])
        self.assertEqual("MIT", portable["license"])
        self.assertNotIn("skills", portable)
        self.assertNotIn("interface", portable)
        self.assertEqual(
            compatibility_before,
            (root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"),
        )
        self.assertTrue(audit_path(root).conforming)

    def test_safe_skill_name_mismatch_is_repaired(self) -> None:
        root = self.make_codex_plugin()
        skill_path = root / "skills" / "check" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace("name: check", "name: wrong"),
            encoding="utf-8",
        )

        result = convert_in_place(root)

        self.assertTrue(result.successful)
        self.assertIn("skills/check/SKILL.md", result.changed_files)
        self.assertIn("name: check", skill_path.read_text(encoding="utf-8"))

    def test_invalid_plugin_name_blocks_conversion(self) -> None:
        root = self.make_codex_plugin("sample")
        manifest_path = root / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["name"] = "Bad Name"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertFalse((root / "plugin.json").exists())
        self.assertIn("conversion-plugin-name", {item.code for item in result.findings})

    def test_claude_stdio_mcp_is_converted_without_changing_source_file(self) -> None:
        root = self.make_codex_plugin()
        source_mcp = {
            "mcpServers": {
                "local": {
                    "command": "python",
                    "args": ["${CLAUDE_PLUGIN_ROOT}/server.py"],
                    "env": {"CONFIG": "${CLAUDE_PLUGIN_ROOT}/config.json"},
                }
            }
        }
        source_path = self.write_json(root, ".mcp.json", source_mcp)
        before = source_path.read_text(encoding="utf-8")

        result = convert_in_place(root)
        portable_mcp = json.loads((root / "mcp.json").read_text(encoding="utf-8"))

        self.assertTrue(result.successful)
        self.assertEqual(before, source_path.read_text(encoding="utf-8"))
        self.assertEqual(MCP_SCHEMA, portable_mcp["$schema"])
        self.assertEqual("stdio", portable_mcp["mcpServers"]["local"]["type"])
        self.assertEqual(
            ["${PLUGIN_ROOT}/server.py"],
            portable_mcp["mcpServers"]["local"]["args"],
        )

    def test_claude_direct_mcp_map_is_converted(self) -> None:
        root = self.make_codex_plugin()
        self.write_json(
            root,
            ".mcp.json",
            {
                "video": {
                    "command": "npx",
                    "args": ["-y", "claude-video-vision@latest"],
                }
            },
        )

        result = convert_in_place(root)
        portable_mcp = json.loads((root / "mcp.json").read_text(encoding="utf-8"))

        self.assertTrue(result.successful)
        self.assertEqual("stdio", portable_mcp["mcpServers"]["video"]["type"])
        self.assertEqual("npx", portable_mcp["mcpServers"]["video"]["command"])

    def test_url_mcp_without_transport_requires_a_choice(self) -> None:
        root = self.make_codex_plugin()
        self.write_json(
            root,
            ".mcp.json",
            {"mcpServers": {"remote": {"url": "https://example.com/mcp"}}},
        )

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertFalse((root / "mcp.json").exists())
        self.assertIn("conversion-mcp-transport", {item.code for item in result.findings})

    def test_prewrite_failure_changes_nothing(self) -> None:
        root = self.make_codex_plugin()
        manifest_path = root / ".codex-plugin" / "plugin.json"
        manifest_before = manifest_path.read_bytes()
        self.write_json(root, ".mcp.json", {"remote": {"url": "https://example.com/mcp"}})

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertEqual(manifest_before, manifest_path.read_bytes())
        self.assertFalse((root / "plugin.json").exists())

    def test_injected_mid_write_failure_restores_original_bytes(self) -> None:
        root = self.make_codex_plugin()
        skill_path = root / "skills" / "check" / "SKILL.md"
        skill_path.write_text(skill_path.read_text(encoding="utf-8").replace("name: check", "name: wrong"), encoding="utf-8")
        original_skill = skill_path.read_bytes()
        original_write = convert_module._atomic_write_text

        def fail_skill(path: Path, text: str) -> bool:
            if path == skill_path:
                raise OSError("injected mid-write failure")
            return original_write(path, text)

        with mock.patch.object(convert_module, "_atomic_write_text", side_effect=fail_skill):
            result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertEqual(original_skill, skill_path.read_bytes())
        self.assertFalse((root / "plugin.json").exists())
        self.assertIn("conversion-transaction", {item.code for item in result.findings})

    def test_dry_run_lists_writes_without_changing_hashes(self) -> None:
        import hashlib

        root = self.make_codex_plugin()
        before = {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file()
        }

        result = convert_in_place(root, dry_run=True)

        after = {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file()
        }
        self.assertTrue(result.successful)
        self.assertTrue(result.dry_run)
        self.assertEqual(["plugin.json"], result.changed_files)
        self.assertEqual(before, after)
        self.assertFalse((root / "plugin.json").exists())

    def test_crlf_bom_manifest_is_not_reported_as_a_write(self) -> None:
        root = self.make_codex_plugin()
        first = convert_in_place(root)
        self.assertTrue(first.successful)
        manifest = root / "plugin.json"
        logical = manifest.read_text(encoding="utf-8")
        manifest.write_bytes(b"\xef\xbb\xbf" + logical.replace("\n", "\r\n").encode("utf-8"))
        before = manifest.read_bytes()

        result = convert_in_place(root, dry_run=True)

        self.assertTrue(result.successful)
        self.assertEqual([], result.changed_files)
        self.assertEqual(before, manifest.read_bytes())

    def test_target_conversion_preserves_empty_directories(self) -> None:
        source = self.base / "source"
        source.mkdir()
        self.write_json(source, ".claude-plugin/plugin.json", {"name": "sample", "version": "1.0.0"})
        self.write_skill(source)
        (source / "references" / "empty").mkdir(parents=True)
        target = self.base / "target"

        result = convert_to_target(source, target)

        self.assertTrue(result.successful)
        self.assertTrue((target / "references" / "empty").is_dir())

    def test_target_conversion_keeps_claude_source_unchanged(self) -> None:
        source = self.base / "source"
        source.mkdir()
        self.write_json(
            source,
            ".claude-plugin/plugin.json",
            {"name": "sample", "version": "1.0.0", "license": "MIT"},
        )
        self.write_skill(source)
        source_snapshot = {
            path.relative_to(source).as_posix(): path.read_bytes()
            for path in source.rglob("*")
            if path.is_file()
        }
        target = self.base / "target"

        result = convert_to_target(source, target)

        self.assertTrue(result.successful)
        self.assertTrue((target / "plugin.json").is_file())
        self.assertTrue((target / ".claude-plugin" / "plugin.json").is_file())
        self.assertEqual(
            source_snapshot,
            {
                path.relative_to(source).as_posix(): path.read_bytes()
                for path in source.rglob("*")
                if path.is_file()
            },
        )

    def test_nonempty_target_is_not_overwritten(self) -> None:
        source = self.make_codex_plugin()
        target = self.base / "occupied"
        target.mkdir()
        sentinel = target / "keep.txt"
        sentinel.write_text("keep\n", encoding="utf-8")

        result = convert_to_target(source, target)

        self.assertFalse(result.successful)
        self.assertEqual("keep\n", sentinel.read_text(encoding="utf-8"))
        self.assertIn("conversion-target-not-empty", {item.code for item in result.findings})

    def test_failed_target_conversion_does_not_leave_partial_target(self) -> None:
        source = self.base / "source"
        source.mkdir()
        self.write_json(
            source,
            ".claude-plugin/plugin.json",
            {"name": "sample", "version": "1.0.0", "license": "MIT"},
        )
        self.write_json(source, ".mcp.json", {"remote": {"url": "https://example.com/mcp"}})
        target = self.base / "target"

        result = convert_to_target(source, target)

        self.assertFalse(result.successful)
        self.assertEqual([], result.changed_files)
        self.assertFalse(target.exists())
        self.assertIn("conversion-mcp-transport", {item.code for item in result.findings})

    def test_marketplace_is_read_only_without_apply(self) -> None:
        marketplace = self.base / "marketplace"
        plugin = marketplace / "plugins" / "sample"
        plugin.mkdir(parents=True)
        self.write_json(plugin, ".codex-plugin/plugin.json", {"name": "sample"})
        self.write_skill(plugin)
        self.write_json(
            marketplace,
            "marketplace.json",
            {
                "name": "sample-marketplace",
                "plugins": [
                    {"name": "sample", "source": {"source": "local", "path": "./plugins/sample"}}
                ],
            },
        )

        dry_results = convert_marketplace(marketplace, apply=False)
        self.assertFalse((plugin / "plugin.json").exists())
        self.assertEqual(1, dry_results[0].error_count)

        applied_results = convert_marketplace(marketplace, apply=True)
        self.assertTrue((plugin / "plugin.json").is_file())
        self.assertTrue(applied_results[0].successful)

    def test_marketplace_refuses_symlink_plugin_path(self) -> None:
        marketplace = self.base / "marketplace"
        plugin = marketplace / "plugins" / "sample"
        plugin.mkdir(parents=True)
        self.write_json(plugin, ".codex-plugin/plugin.json", {"name": "sample"})
        self.write_skill(plugin)
        linked = marketplace / "plugins" / "linked"
        try:
            os.symlink(plugin, linked, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        self.write_json(
            marketplace,
            "marketplace.json",
            {
                "name": "sample-marketplace",
                "plugins": [
                    {"name": "linked", "source": {"source": "local", "path": "./plugins/linked"}}
                ],
            },
        )

        results = convert_marketplace(marketplace, apply=True)

        self.assertFalse(results[0].successful)
        self.assertIn("conversion-link", {item.code for item in results[0].findings})
        self.assertTrue(linked.is_symlink())
        self.assertFalse((plugin / "plugin.json").exists())

    def test_conversion_rejects_symlinked_codex_manifest_directory(self) -> None:
        root = self.base / "codex"
        root.mkdir()
        outside = self.base / "outside"
        (outside / ".codex-plugin").mkdir(parents=True)
        self.write_json(outside, ".codex-plugin/plugin.json", {"name": "sample"})
        self.link_directory(outside / ".codex-plugin", root / ".codex-plugin")

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertIn("conversion-link", {item.code for item in result.findings})
        self.assertFalse((root / "plugin.json").exists())

    def test_conversion_rejects_symlinked_claude_manifest_directory(self) -> None:
        root = self.base / "claude"
        root.mkdir()
        outside = self.base / "outside"
        (outside / ".claude-plugin").mkdir(parents=True)
        self.write_json(outside, ".claude-plugin/plugin.json", {"name": "sample"})
        self.link_directory(outside / ".claude-plugin", root / ".claude-plugin")

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertIn("conversion-link", {item.code for item in result.findings})
        self.assertFalse((root / "plugin.json").exists())

    def test_conversion_rejects_symlinked_skills_directory(self) -> None:
        root = self.make_codex_plugin()
        skill_path = root / "skills" / "check" / "SKILL.md"
        skill_path.unlink()
        skill_path.parent.rmdir()
        root.joinpath("skills").rmdir()
        outside = self.base / "outside"
        outside.mkdir()
        self.link_directory(outside, root / "skills")

        result = convert_in_place(root)

        self.assertFalse(result.successful)
        self.assertIn("conversion-link", {item.code for item in result.findings})
        self.assertFalse((root / "plugin.json").exists())

    def test_transaction_validation_reports_the_failed_operation(self) -> None:
        root = self.base / "root"
        root.mkdir()
        linked_parent = root / "linked"
        outside = self.base / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, linked_parent, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        operation = linked_parent / "output.txt"
        transaction = FileTransaction(root)
        transaction.add_text(operation, "output\n", convert_module._atomic_write_text)

        with self.assertRaises(TransactionError) as raised:
            transaction.commit()

        self.assertEqual(operation, raised.exception.operation)
        self.assertIn("output.txt", str(raised.exception))
        self.assertFalse((outside / "output.txt").exists())

    def test_transaction_recovery_refuses_swapped_parent_link(self) -> None:
        root = self.base / "root"
        root.mkdir()
        parent = root / "new"
        parent.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        try:
            probe = self.base / "symlink-probe"
            os.symlink(outside, probe, target_is_directory=True)
            probe.unlink()
        except OSError as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        operation = parent / "output.txt"
        transaction = FileTransaction(root)

        def swap_parent(path: Path, text: str) -> None:
            path.write_text(text, encoding="utf-8")
            path.unlink()
            parent.rmdir()
            os.symlink(outside, parent, target_is_directory=True)
            raise OSError("injected failure after parent swap")

        transaction.add_text(operation, "output\n", swap_parent)

        with self.assertRaises(TransactionError) as raised:
            transaction.commit()

        self.assertIsNotNone(raised.exception.recovery)
        self.assertTrue(parent.is_symlink())
        self.assertFalse((outside / "output.txt").exists())


if __name__ == "__main__":
    unittest.main()
