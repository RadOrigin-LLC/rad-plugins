from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


CONVERTER_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = CONVERTER_ROOT.parents[1]
SCRIPTS_DIR = CONVERTER_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit import PLUGIN_SCHEMA, audit_path


class RadCoolifyPackageTests(unittest.TestCase):
    def test_rad_coolify_is_a_public_codex_agent_plugin(self) -> None:
        plugin_root = REPOSITORY_ROOT / "plugins" / "rad-coolify"
        portable = json.loads((plugin_root / "plugin.json").read_text(encoding="utf-8"))
        codex = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        portable_mcp = json.loads((plugin_root / "mcp.json").read_text(encoding="utf-8"))

        self.assertEqual(PLUGIN_SCHEMA, portable["$schema"])
        self.assertEqual("rad-coolify", portable["name"])
        self.assertIsInstance(portable["version"], str)
        self.assertTrue(portable["version"])
        self.assertEqual(portable["version"], codex["version"])
        self.assertEqual("MIT", portable["license"])
        self.assertEqual("rad-coolify", codex["name"])
        self.assertEqual("./skills/", codex["skills"])
        self.assertEqual("./.mcp.json", codex["mcpServers"])
        self.assertEqual("stdio", portable_mcp["mcpServers"]["coolify"]["type"])

        skill_names = {
            path.parent.name for path in (plugin_root / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(10, len(skill_names))
        self.assertIn("coolify-review", skill_names)
        native_claude = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(portable["name"], native_claude["name"])
        self.assertEqual(portable["version"], native_claude["version"])
        self.assertEqual("./skills/", native_claude["skills"])
        self.assertEqual("./.mcp.json", native_claude["mcpServers"])
        for obsolete in ("agents", "hooks"):
            self.assertFalse((plugin_root / obsolete).exists())

        report = audit_path(plugin_root)
        self.assertTrue(report.conforming, [item.to_dict() for item in report.findings])

        catalogs = [
            json.loads((REPOSITORY_ROOT / "marketplace.json").read_text(encoding="utf-8")),
            json.loads((REPOSITORY_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")),
        ]
        self.assertEqual(catalogs[0], catalogs[1])
        entry = next(item for item in catalogs[0]["plugins"] if item["name"] == "rad-coolify")
        self.assertEqual("./plugins/rad-coolify", entry["source"]["path"])

    def test_rad_coolify_readme_explains_safe_mcp_setup(self) -> None:
        readme = (
            REPOSITORY_ROOT / "plugins" / "rad-coolify" / "README.md"
        ).read_text(encoding="utf-8")

        required_text = (
            "Security > API Tokens",
            "COOLIFY_URL",
            "COOLIFY_API_TOKEN",
            "SetEnvironmentVariable",
            "read:sensitive",
            "https://coolify.io/docs/api-reference/authorization",
            "codex plugin add rad-coolify@radesjardins-codex-skills",
            "Node.js 18",
            "/api/v1",
            "/mcp",
        )
        for text in required_text:
            self.assertIn(text, readme)


if __name__ == "__main__":
    unittest.main()
