#!/usr/bin/env python3
"""Focused regression tests for secret-safe Dockerfile findings."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[1]
LINTER = PACKAGE_ROOT / "scripts" / "lint-dockerfile.py"


def run_linter(dockerfile: str, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "Dockerfile"
        path.write_text(dockerfile, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(LINTER), str(path), *args],
            check=False,
            capture_output=True,
            text=True,
        )


def test_literal_secret_is_never_echoed() -> None:
    secret = "sk_live_1234567890abcdef"
    result = run_linter(
        "\n".join(
            [
                "FROM node:20-alpine",
                f"ENV API_KEY={secret}",
                "USER node",
                "EXPOSE 3000",
                "HEALTHCHECK CMD node -e \"process.exit(0)\"",
            ]
        )
        + "\n",
        "--json",
    )

    assert result.returncode == 1
    assert secret not in result.stdout
    assert secret not in result.stderr
    report = json.loads(result.stdout)
    finding_text = json.dumps(report)
    assert "API_KEY" in finding_text
    assert '"line": 2' in finding_text


def test_secret_shaped_value_finding_names_key_without_value() -> None:
    secret = "A" * 48
    result = run_linter(
        "\n".join(
            [
                "FROM node:20-alpine",
                f"ENV BUILD_SETTING={secret}",
                "USER node",
                "EXPOSE 3000",
                "HEALTHCHECK CMD node -e \"process.exit(0)\"",
            ]
        )
        + "\n"
    )

    assert result.returncode == 1
    assert secret not in result.stdout
    assert "BUILD_SETTING" in result.stdout
    assert "L2" in result.stdout


if __name__ == "__main__":
    test_literal_secret_is_never_echoed()
    test_secret_shaped_value_finding_names_key_without_value()
    print("2 focused lint tests passed")
