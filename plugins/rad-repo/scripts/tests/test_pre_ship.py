#!/usr/bin/env python3
"""Regression tests for staged-change pre-ship safety."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "pre_ship.py"
DOCTOR = Path(__file__).resolve().parents[1] / "repo-doctor.py"


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    )


def scan(files, config=None, extra_args=None, unstaged_files=None, approve=False, json_output=True):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.com")
        git(root, "config", "user.name", "Test")
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        if config:
            (root / ".rad-repo.json").write_text(json.dumps(config), encoding="utf-8")
            scopes = config.get("validation", {}).get("scopes", {})
            for scope in scopes:
                scope_path = root / scope
                if not scope_path.suffix:
                    scope_path.mkdir(parents=True, exist_ok=True)
        git(root, "add", "-f", "--", ".")
        if approve:
            approval = subprocess.run(
                [sys.executable, str(DOCTOR), str(root), "--approve", "--json"],
                capture_output=True, text=True, check=False,
            )
            assert approval.returncode == 0, approval.stdout + approval.stderr
        for relative, content in (unstaged_files or {}).items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        command = [sys.executable, str(SCRIPT), str(root)]
        if json_output:
            command.append("--json")
        command.extend(extra_args or [])
        result = subprocess.run(
            command,
            capture_output=True, text=True, check=False,
        )
        if json_output:
            return result.returncode, json.loads(result.stdout)
        return result.returncode, result.stdout + result.stderr


code, report = scan({".env": "SECRET=value\n"})
assert code == 1 and report["blocking"], report
assert report["findings"][0]["kind"] == "protected_path", report

code, report = scan({".env.example": "SECRET=placeholder\n", "src/app.py": "print('ok')\n"})
assert code == 0 and not report["findings"], report

code, report = scan({"dist/bundle.js": "generated\n"})
assert code == 1, report
assert report["findings"][0]["kind"] == "generated_output", report

private_key_marker = "-----BEGIN " + "PRIVATE KEY-----\nsecret\n"
code, report = scan({"cert.txt": private_key_marker})
assert code == 1, report
assert report["findings"][0]["kind"] == "secret_content", report

code, report = scan(
    {"large.txt": "x" * 32},
    {"shipping": {"large_file_bytes": 16}},
    ["--allow-contract-change"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "large_file", report

code, report = scan(
    {"AGENTS.md": "# Instructions\n\n- Test: `echo safe`\n"},
    extra_args=["--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "contract_change", report
assert report["validation"] == [], "blocked contract commands must never execute"

code, report = scan(
    {"safe.txt": "safe"},
    extra_args=["--run-validation"],
    unstaged_files={"AGENTS.md": "# Instructions\n\n- Test: `echo unsafe`\n"},
)
assert code == 1, report
assert any(item["kind"] == "contract_dirty" for item in report["findings"]), report
assert report["validation"] == [], "unstaged contract commands must never execute"

code, report = scan(
    {"AGENTS.md": "# Instructions\n\n- Test: `echo safe`\n"},
    extra_args=["--allow-contract-change"],
)
assert code == 0, report

code, report = scan({"README.md": "docs only\n"}, extra_args=["--run-validation"])
assert code == 1, report
assert report["findings"][0]["kind"] == "validation_missing", report

code, report = scan(
    {"AGENTS.md": "# Instructions\n\n- Test: `echo safe`\n", "safe.txt": "safe\n"},
    extra_args=["--allow-contract-change", "--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "validation_untrusted", report
assert report["validation"] == [], "unapproved commands must never execute"

code, report = scan(
    {"AGENTS.md": "# Instructions\n\n- Test: `echo safe`\n", "safe.txt": "safe\n"},
    extra_args=["--allow-contract-change", "--run-validation"],
    approve=True,
)
assert code == 0, report
assert report["validation"][0]["returncode"] == 0, report
assert isinstance(report["validation"][0]["duration_ms"], int), report
assert report["validation"][0]["duration_ms"] >= 0, report
assert report["validation"][0]["output_redacted"] is True, report
assert "output_tail" not in report["validation"][0], report
assert isinstance(report["timing"]["total_ms"], int), report
assert report["timing"]["validation_ms"] >= report["validation"][0]["duration_ms"], report

code, report = scan(
    {"src/app.py": "print('scoped')\n"},
    {"validation": {"scopes": {".rad-repo.json": ["echo scoped"], "src": ["echo scoped"]}, "allow_empty": False}},
    ["--allow-contract-change", "--run-validation"],
    approve=True,
)
assert code == 0, report
assert report["validation_contract"]["commands"][0]["command"] == "echo scoped", report
assert report["validation"][0]["command"] == "echo scoped", report

contract_config = {
    "validation": {
        "scopes": {
            ".rad-repo.json": ["echo contract"],
            "src": ["echo scoped"],
        },
        "allow_empty": False,
    }
}
code, report = scan(
    {"src/app.py": "print('contract')\n"},
    contract_config,
    ["--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "contract_change", report
assert report["validation"] == [], report

code, report = scan(
    {"src/app.py": "print('contract')\n"},
    contract_config,
    ["--allow-contract-change", "--run-validation"],
    approve=True,
)
assert code == 0, report
assert report["validation_contract"]["unmatched_paths"] == [], report
assert {item["command"] for item in report["validation_contract"]["commands"]} == {
    "echo contract", "echo scoped"
}, report

code, report = scan(
    {"src/app.py": "print('scoped')\n", "docs/readme.md": "docs only\n"},
    {"validation": {"scopes": {".rad-repo.json": ["echo scoped"], "src": ["echo scoped"]}, "allow_empty": False}},
    ["--allow-contract-change", "--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "validation_missing", report
assert report["validation_contract"]["commands"][0]["command"] == "echo scoped", report
assert report["validation_contract"]["unmatched_paths"] == ["docs/readme.md"], report
assert report["validation"] == [], report

code, report = scan(
    {"docs/readme.md": "docs only\n"},
    {"validation": {"scopes": {".rad-repo.json": ["echo scoped"], "src": ["echo scoped"]}, "allow_empty": False}},
    ["--allow-contract-change", "--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "validation_missing", report
assert report["validation_contract"]["commands"][0]["command"] == "echo scoped", report
assert report["validation_contract"]["allow_empty"] is False, report
assert report["validation"] == [], report

code, report = scan(
    {"README.md": "docs only\n"},
    {"validation": {"scopes": {}, "allow_empty": False}},
    ["--allow-contract-change", "--run-validation"],
)
assert code == 1, report
assert report["findings"][0]["kind"] == "validation_missing", report
assert report["validation_contract"]["commands"] == [], report

code, report = scan(
    {"README.md": "docs only\n"},
    {"validation": {"allow_empty": True}},
    ["--allow-contract-change", "--run-validation"],
)
assert code == 0, report

validation_secret = "DISTINCTIVE_VALIDATION_OUTPUT_SECRET_8F3A"
validation_files = {
    "check.py": (
        "import sys\n"
        f"print({validation_secret!r})\n"
        f"print({validation_secret!r}, file=sys.stderr)\n"
    ),
}
validation_config = {
    "validation": {
        "scopes": {
            ".rad-repo.json": ["python check.py"],
            "check.py": ["python check.py"],
        },
        "allow_empty": False,
    }
}
code, report = scan(
    validation_files,
    validation_config,
    ["--allow-contract-change", "--run-validation"],
    approve=True,
)
assert code == 0, report
assert report["validation"][0]["command"] == "python check.py", report
assert report["validation"][0]["output_redacted"] is True, report
assert validation_secret not in json.dumps(report), report

code, rendered = scan(
    validation_files,
    validation_config,
    ["--allow-contract-change", "--run-validation"],
    approve=True,
    json_output=False,
)
assert code == 0, rendered
assert validation_secret not in rendered, rendered
assert "validation output redacted" in rendered, rendered

print("pre-ship regression tests passed")
