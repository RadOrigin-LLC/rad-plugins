import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[1]
README = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
BRIDGE = (PACKAGE_ROOT / "skills" / "hemingway-bridge" / "SKILL.md").read_text(encoding="utf-8")


class ParaSourceContractTests(unittest.TestCase):
    def test_rad_repo_offer_is_gated_and_standalone_fallback_is_explicit(self):
        for source in (README, BRIDGE):
            self.assertIn("exact needed", source)
            self.assertIn("current available-skill list", source)
            self.assertIn("current task needs", source)
            self.assertIn("user accepts", source)
            self.assertIn("exact skill is absent", source)
            self.assertIn("user declines", source)
            self.assertIn("standalone", source)

        self.assertNotIn("When RAD Repo is installed", README)
        self.assertNotIn("reads it for you", BRIDGE)
        self.assertNotIn("reads the handoff automatically", BRIDGE)
        self.assertNotIn("installed", BRIDGE)


if __name__ == "__main__":
    unittest.main()
