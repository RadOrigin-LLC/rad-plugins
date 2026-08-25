import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def read(self, relative_path):
        return (PLUGIN_ROOT / relative_path).read_text(encoding="utf-8")

    def test_manifest_and_public_skill_name_match_4_1(self):
        manifest = json.loads(self.read(".codex-plugin/plugin.json"))
        self.assertEqual("4.1.2", manifest["version"])
        self.assertTrue((PLUGIN_ROOT / "skills" / "software-design" / "SKILL.md").is_file())
        self.assertFalse((PLUGIN_ROOT / "skills" / "design-sprint" / "SKILL.md").exists())

        package_text = self.read(".codex-plugin/plugin.json") + self.read("README.md")
        self.assertNotIn("design-sprint", package_text)
        self.assertIn("rad-brainstorm:software-design", package_text)

    def test_public_scope_is_one_person_and_text_first(self):
        readme = self.read("README.md").lower()
        self.assertIn("one-person", readme)
        self.assertIn("text-first", readme)

    def test_brainstorm_workflow_has_4_1_quality_controls(self):
        skill = self.read("skills/brainstorm-session/SKILL.md").lower()
        for phrase in (
            "goal",
            "primary user",
            "success",
            "hard constraint",
            "[user]",
            "[ai]",
            "[research]",
            "mechanism",
            "cluster",
            "checkpoint",
            "mermaid",
            "session-output.md",
        ):
            self.assertIn(phrase, skill)

    def test_behavior_cases_have_matching_source_contracts(self):
        cases = self.read("tests/behavior-cases.md").lower()
        case_contracts = {
            "user-input-before-suggestions": (
                "ask what the user has considered before offering ideas",
                "keep the user's starting ideas ahead of ai suggestions",
            ),
            "stable-idea-ids": (
                "assign every idea a stable id such as `i1`",
                "preserve the original id and wording when ideas are grouped",
                "ask before merging ideas that differ in audience, mechanism, channel, cost, or risk",
            ),
            "disclosed-source-labels": (
                "label each idea `[user]`, `[ai]`, or `[research]`",
                "keep source labels attached when ideas are grouped or evaluated",
                "keep user ideas visible in the final result",
            ),
            "saved-repository-path": (
                "repeat the exact repository path",
                "ask for user approval before writing",
                "do not silently substitute a destination",
                "keep `docs/design.md` protected",
            ),
            "user-provided-research-or-design-evidence": (
                "read user-provided research or design evidence from the path or content the user names",
                "keep the exact path or link, claims, and source label",
                "mark conflicts and unknowns instead of inventing support",
                "ask before adding outside research",
            ),
            "stop-before-plan-or-code": (
                "stop before implementation planning or code",
                "offer a planning companion only under the companion-skill rule",
            ),
            "companion-loaded-skill-and-user-acceptance": (
                "match the exact skill name against the current available-skill list",
                "ask whether the user accepts the companion",
                "invoke it only after the user asks or accepts",
                "continue without it when the exact skill is absent or the user declines",
            ),
        }
        for case_id, phrases in case_contracts.items():
            self.assertIn(f"## {case_id}", cases)
            for phrase in phrases:
                self.assertIn(phrase, cases)

        session = self.read("skills/brainstorm-session/SKILL.md").lower()
        design = self.read("skills/software-design/SKILL.md").lower()
        for phrase in (
            "ask what the user has considered before offering ideas",
            "preserve the user's wording, original ids, and source labels",
            "[user]",
            "[ai]",
            "[research]",
            "user-provided research or design evidence",
            "repeat the exact repository path",
            "do not silently substitute a destination",
            "stop before implementation planning or code",
        ):
            self.assertIn(phrase, session)

        self.assertIn("user-provided research or design evidence", design)
        self.assertIn("repeat the exact repository path", design)
        self.assertIn("mark conflicts and unknowns instead of inventing support", design)
        self.assertIn("stop before implementation planning or code", design)
        for source in (session, design):
            self.assertIn("the exact skill appears in the current available-skill list", source)
            self.assertIn("user accepts", source)
        self.assertIn("if the exact skill is absent or the user declines, continue the current brainstorm workflow standalone", session)
        self.assertIn("if the exact skill is absent or the user declines, continue the current software-design workflow standalone", design)

    def test_evaluation_workflow_protects_distinctions_and_sets_proof_thresholds(self):
        skill = self.read("skills/idea-evaluation/SKILL.md").lower()
        self.assertIn("cluster", skill)
        self.assertIn("preserve", skill)
        self.assertIn("pass threshold", skill)
        self.assertIn("stop signal", skill)

    def test_references_are_smaller_and_have_one_source_of_truth(self):
        references = PLUGIN_ROOT / "references"
        self.assertFalse((references / "domain-research-guide.md").exists())

        facilitation = self.read("references/facilitation-principles.md")
        methods = self.read("references/methodology-catalog.md")
        unblocking = self.read("references/creative-unblocking.md")
        evaluation = self.read("references/evaluation-frameworks.md")

        self.assertLess(len(facilitation.split()), 900)
        self.assertLess(len(methods.split()), 2200)
        self.assertNotIn("## Convergent Techniques", methods)
        self.assertNotIn("### 9. 5 Whys", methods)
        self.assertNotIn("## 7. SWOT", evaluation)
        self.assertNotIn("Barry Schwartz", unblocking)
        self.assertNotIn("consistently shows", facilitation.lower())

    def test_result_contract_has_three_examples_and_checkpoint_fields(self):
        result_contract = self.read("references/session-output.md").lower()
        for heading in ("## result contract", "## example 1", "## example 2", "## example 3"):
            self.assertIn(heading, result_contract)
        for field in ("session phase", "next question", "idea source", "user approval"):
            self.assertIn(field, result_contract)


if __name__ == "__main__":
    unittest.main()
