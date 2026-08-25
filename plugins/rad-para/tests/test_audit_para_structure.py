import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "audit-para-structure.py"
SPEC = importlib.util.spec_from_file_location("audit_para_structure", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class AuditParaStructureTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "para"
        self.root.mkdir()

    def tearDown(self):
        self.tempdir.cleanup()

    def make_categories(self, names):
        for name in names:
            (self.root / name).mkdir()

    def test_plain_numbered_plural_optional_and_case_variants_are_accepted(self):
        self.make_categories(["1-Projects", "2 Areas", "3_Resources", "4-ARCHIVES", "0 inbox", "5 TEMPLATES"])
        findings = []
        summary = AUDIT.audit(self.root, findings=findings, project_min=0, project_max=0)

        self.assertEqual(summary["canonical_missing"], [])
        self.assertEqual(summary["extra_top_level"], [])
        self.assertEqual(summary["optional_present"], ["inbox", "templates"])
        self.assertEqual(summary["active_project_count"], 0)
        self.assertFalse([f for f in findings if f.severity in {"critical", "warning"}])

    def test_resource_topics_are_valid(self):
        self.make_categories(["Projects", "Areas", "Resources", "Archive"])
        (self.root / "Resources" / "Birds").mkdir()
        (self.root / "Resources" / "Photography").mkdir()
        findings = []
        AUDIT.audit(self.root, findings=findings, project_min=0, project_max=0)

        self.assertFalse([f for f in findings if f.path.endswith("Birds") or f.path.endswith("Photography")])

    def test_project_count_is_configurable_advice(self):
        self.make_categories(["Projects", "Areas", "Resources", "Archive"])
        (self.root / "Projects" / "Launch site").mkdir()
        findings = []
        summary = AUDIT.audit(self.root, findings=findings, project_min=1, project_max=2)

        self.assertEqual(summary["project_count_advice"]["status"], "within")
        self.assertFalse([f for f in findings if f.code == "project_count_advice"])

        findings = []
        summary = AUDIT.audit(self.root, findings=findings, project_min=2, project_max=3)
        self.assertEqual(summary["project_count_advice"]["status"], "below")
        count_findings = [f for f in findings if f.code == "project_count_advice"]
        self.assertEqual(len(count_findings), 1)
        self.assertEqual(count_findings[0].severity, "info")

    def test_incomplete_reads_are_reported(self):
        self.make_categories(["Projects", "Areas", "Resources", "Archive"])
        findings = []
        with mock.patch.object(AUDIT.Path, "iterdir", side_effect=PermissionError("denied")):
            summary = AUDIT.audit(self.root, findings=findings, project_min=0, project_max=0)

        self.assertEqual(len(summary["incomplete_reads"]), 1)
        self.assertTrue(any(f.code == "incomplete_read" for f in findings))

    def test_inaccessible_child_entry_is_reported(self):
        self.make_categories(["Projects", "Areas", "Resources", "Archive"])
        broken = self.root / "Projects" / "broken-child"
        broken.mkdir()
        original_lstat = AUDIT.Path.lstat

        def fail_for_child(path):
            if path == broken:
                raise PermissionError("child denied")
            return original_lstat(path)

        findings = []
        with mock.patch.object(AUDIT.Path, "lstat", fail_for_child):
            summary = AUDIT.audit(self.root, findings=findings, project_min=0, project_max=0)

        self.assertTrue(any(item["path"].endswith("broken-child") for item in summary["incomplete_reads"]))
        self.assertTrue(any(f.code == "incomplete_read" and f.path.endswith("broken-child") for f in findings))

    def test_links_are_not_traversed(self):
        self.make_categories(["Projects", "Areas", "Resources", "Archive"])
        visible_if_followed = self.root / "Areas" / "visible-only-if-followed.md"
        visible_if_followed.write_text("secret", encoding="utf-8")
        link = self.root / "Projects" / "linked-area"
        try:
            link.symlink_to(self.root / "Areas", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlinks are unavailable")

        findings = []
        summary = AUDIT.audit(self.root, findings=findings, project_min=0, project_max=0)

        self.assertEqual(summary["active_project_count"], 0)
        self.assertTrue(summary["skipped_links"] or any(f.code == "outside_root" for f in findings))
        self.assertNotIn("visible-only-if-followed.md", json.dumps(summary))


if __name__ == "__main__":
    unittest.main()
