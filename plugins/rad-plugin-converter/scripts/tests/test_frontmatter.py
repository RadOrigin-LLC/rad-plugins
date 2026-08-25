from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter import audit_frontmatter, parse_frontmatter, repair_skill_name


class FrontmatterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def make_skill(self, directory: str, frontmatter: str, body: str = "# Test\n") -> Path:
        skill_dir = self.root / "skills" / directory
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\n{frontmatter}\n---\n\n{body}",
            encoding="utf-8",
        )
        return skill_dir

    def finding_codes(self, skill_dir: Path) -> set[str]:
        return {item.code for item in audit_frontmatter(skill_dir, self.root)}

    def test_valid_folded_description_matches_directory(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            "name: audit-plugin\n"
            "description: >\n"
            "  Audit plugins and skills. Use when checking Agent Plugins conformance.\n"
            "license: MIT\n"
            "compatibility: Requires Python 3.10 or newer.\n"
            "metadata:\n"
            "  author: RAD\n"
            '  version: "1.0"\n'
            "allowed-tools: Read Shell",
        )

        self.assertEqual([], audit_frontmatter(skill, self.root))
        document = parse_frontmatter(skill / "SKILL.md")
        self.assertEqual("audit-plugin", document.values["name"])
        self.assertIn("Use when", document.values["description"])
        self.assertEqual({"author": "RAD", "version": "1.0"}, document.values["metadata"])

    def test_yaml_metadata_accepts_quoted_dotted_keys_and_comments(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            'name: audit-plugin\n'
            'description: "Audit # plugins without changing them."\n'
            "metadata: # metadata entries follow\n"
            "  # A YAML comment is allowed here.\n"
            '  "com.example/version": \'1.0\' # trailing comment\n'
            '  com.example.name: "RAD"\n'
            '  "display.name": \'A quoted value\'\n',
        )

        self.assertEqual([], audit_frontmatter(skill, self.root))
        document = parse_frontmatter(skill / "SKILL.md")
        self.assertEqual(
            {
                "com.example/version": "1.0",
                "com.example.name": "RAD",
                "display.name": "A quoted value",
            },
            document.values["metadata"],
        )

    def test_unsupported_fallback_syntax_is_labeled(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            "name: audit-plugin\n"
            "description: Use when auditing plugins.\n"
            "metadata:\n"
            "  nested:\n"
            "    value: unsupported\n",
        )

        findings = audit_frontmatter(skill, self.root)
        self.assertIn("skill-frontmatter", {item.code for item in findings})
        self.assertIn("Unsupported YAML fallback syntax", findings[0].message)

    def test_name_mismatch_is_reported_and_can_be_repaired(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            "name: wrong-name\ndescription: Use when auditing plugins.",
        )

        self.assertIn("skill-name-mismatch", self.finding_codes(skill))
        self.assertTrue(repair_skill_name(skill))
        self.assertNotIn("skill-name-mismatch", self.finding_codes(skill))
        self.assertFalse(repair_skill_name(skill))

    def test_metadata_values_must_be_strings(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            "name: audit-plugin\n"
            "description: Use when auditing plugins.\n"
            "metadata:\n"
            "  count: 3",
        )

        self.assertIn("skill-metadata-value", self.finding_codes(skill))

    def test_unknown_top_level_field_is_reported(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            "name: audit-plugin\n"
            "description: Use when auditing plugins.\n"
            "argument-hint: path",
        )

        self.assertIn("skill-unknown-field", self.finding_codes(skill))

    def test_missing_closing_delimiter_is_reported(self) -> None:
        skill_dir = self.root / "skills" / "audit-plugin"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: audit-plugin\ndescription: Use when auditing plugins.\n",
            encoding="utf-8",
        )

        self.assertIn("skill-frontmatter", self.finding_codes(skill_dir))

    def test_description_limit_is_enforced(self) -> None:
        skill = self.make_skill(
            "audit-plugin",
            f"name: audit-plugin\ndescription: {'x' * 1025}",
        )

        self.assertIn("skill-description-length", self.finding_codes(skill))


if __name__ == "__main__":
    unittest.main()
