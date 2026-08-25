import importlib.util
import json
import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN_ROOT / "scripts" / "validate-json.py"
SCHEMAS = PLUGIN_ROOT / "references" / "subagent-prompts"


def load_validator():
    spec = importlib.util.spec_from_file_location("rad_plan_validate_json", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = load_validator()


class ValidateJsonTests(unittest.TestCase):
    def test_valid_stack_payload(self):
        schema = self.schema("stack-eval.schema.json")
        payload = {
            "evaluation_complete": True,
            "project_type": "existing web app",
            "summary": "Keep the current stack.",
            "current_stack_fit": "fits",
            "recommendation": [{
                "layer": "Application",
                "choice": "Current stack",
                "version": "repository versions",
                "requirement": "Add one settings field",
                "rationale": "No new system is required.",
            }],
            "compatibility_verified": True,
            "verification_sources": [{
                "title": "Python documentation",
                "url": "https://docs.python.org/3/",
                "checked_on": "2026-08-22",
            }],
            "confidence": "high",
            "escalation_required": False,
        }
        self.assertEqual([], validator.validate(payload, schema))

    def test_stack_payload_requires_requirement(self):
        schema = self.schema("stack-eval.schema.json")
        payload = {
            "evaluation_complete": True,
            "project_type": "new app",
            "summary": "Choose one option.",
            "current_stack_fit": "no_current_stack",
            "recommendation": [{
                "layer": "Database",
                "choice": "PostgreSQL",
                "version": "18",
                "rationale": "Fits the data model.",
            }],
            "compatibility_verified": True,
            "confidence": "medium",
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("requirement" in error["path"] for error in errors), errors)

    def test_verified_stack_payload_requires_sources(self):
        schema = self.schema("stack-eval.schema.json")
        payload = {
            "evaluation_complete": True,
            "project_type": "existing web app",
            "summary": "Keep the current stack.",
            "current_stack_fit": "fits",
            "recommendation": [{
                "layer": "Application",
                "choice": "Current stack",
                "version": "repository versions",
                "requirement": "Add one settings field",
                "rationale": "No new system is required.",
            }],
            "compatibility_verified": True,
            "verification_sources": [],
            "confidence": "high",
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("verification_sources" in error["path"] for error in errors), errors)

    def test_blocking_issue_rejects_medium_severity(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "REVISE",
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 1,
                "low_count": 0,
            },
            "blocking_issues": [{
                "task_id": "T1",
                "category": "context",
                "severity": "MEDIUM",
                "issue": "Context is incomplete.",
                "fix": "Add the missing context.",
            }],
            "advisory_issues": [],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("blocking_issues" in error["path"] for error in errors), errors)

    def test_blocking_issue_rejects_low_severity(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "REVISE",
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 1,
            },
            "blocking_issues": [{
                "task_id": "T1",
                "category": "context",
                "severity": "LOW",
                "issue": "Context could be clearer.",
                "fix": "Clarify the context.",
            }],
            "advisory_issues": [],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("blocking_issues" in error["path"] for error in errors), errors)

    def test_blocking_issue_accepts_high_severity(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "REVISE",
            "summary": {
                "critical_count": 0,
                "high_count": 1,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [{
                "task_id": "T1",
                "category": "tdd",
                "severity": "HIGH",
                "issue": "The outcome lacks a required test.",
                "fix": "Add the test before implementation.",
            }],
            "advisory_issues": [],
            "escalation_required": False,
        }
        self.assertEqual([], validator.validate(payload, schema))

    def test_risk_summary_counts_match_issue_arrays(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "REVISE",
            "summary": {
                "critical_count": 0,
                "high_count": 1,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [{
                "task_id": "T1",
                "category": "tdd",
                "severity": "CRITICAL",
                "issue": "A required test is missing.",
                "fix": "Add the test.",
            }],
            "advisory_issues": [],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("critical_count" in error["path"] for error in errors), errors)

    def test_approve_rejects_critical_issue(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "APPROVE",
            "summary": {
                "critical_count": 1,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [{
                "task_id": "T1",
                "category": "failure-state",
                "severity": "CRITICAL",
                "issue": "Recovery can lose data.",
                "fix": "Add a recoverable path.",
            }],
            "advisory_issues": [],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("APPROVE" in error["message"] for error in errors), errors)

    def test_approve_rejects_summary_only_critical_and_high_counts(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "APPROVE",
            "summary": {
                "critical_count": 1,
                "high_count": 1,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [],
            "advisory_issues": [],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("APPROVE" in error["message"] for error in errors), errors)

    def test_advisory_issue_counts_match_summary(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "REVISE",
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [],
            "advisory_issues": [{
                "task_id": "T2",
                "category": "context",
                "severity": "LOW",
                "issue": "The note could be clearer.",
                "fix": "Clarify the note.",
            }],
            "escalation_required": False,
        }
        errors = validator.validate(payload, schema)
        self.assertTrue(any("low_count" in error["path"] for error in errors), errors)

    def test_unverified_stack_payload_allows_empty_sources(self):
        schema = self.schema("stack-eval.schema.json")
        payload = {
            "evaluation_complete": True,
            "project_type": "existing web app",
            "summary": "Compatibility remains unverified.",
            "current_stack_fit": "partly_fits",
            "recommendation": [{
                "layer": "Application",
                "choice": "Current stack",
                "version": "repository versions",
                "requirement": "Keep the current deployment",
                "rationale": "No source was available to verify compatibility.",
            }],
            "compatibility_verified": False,
            "verification_sources": [],
            "confidence": "low",
            "escalation_required": True,
            "escalation_reason": "Compatibility needs owner review.",
        }
        self.assertEqual([], validator.validate(payload, schema))

    def test_valid_risk_payload(self):
        schema = self.schema("risk-assessment.schema.json")
        payload = {
            "assessment_complete": True,
            "iteration": 1,
            "verdict": "APPROVE",
            "summary": {
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "blocking_issues": [],
            "advisory_issues": [],
            "escalation_required": False,
        }
        self.assertEqual([], validator.validate(payload, schema))

    def test_extracts_json_code_block(self):
        raw = "before\n```json\n{\"valid\": true}\n```\nafter"
        self.assertEqual('{"valid": true}', validator.extract_json_from_markdown(raw))

    @staticmethod
    def schema(name: str) -> dict:
        return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
