#!/usr/bin/env python3
"""Focused contract checks for the RAD Coolify package."""

from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).parents[1]
SKILLS_ROOT = PACKAGE_ROOT / "skills"
REQUIRED_SKILLS = {
    "coolify-actions",
    "coolify-cicd",
    "coolify-databases",
    "coolify-deploy",
    "coolify-infrastructure",
    "coolify-observability",
    "coolify-review",
    "coolify-security",
    "coolify-status",
    "coolify-troubleshoot",
}

CHANGED_SKILLS = (
    "coolify-cicd",
    "coolify-deploy",
    "coolify-infrastructure",
    "coolify-observability",
    "coolify-security",
    "coolify-status",
    "coolify-troubleshoot",
)

DIRECTLY_LINKED_REFERENCES = (
    "coolify-cicd/references/api-reference.md",
    "coolify-cicd/references/gitlab-ci-pattern.md",
    "coolify-deploy/references/registry-patterns.md",
    "coolify-deploy/references/build-packs.md",
    "coolify-infrastructure/references/multi-server-setup.md",
    "coolify-infrastructure/references/swarm-guide.md",
    "coolify-observability/references/log-drain-configs.md",
    "coolify-observability/references/grafana-prometheus-setup.md",
    "coolify-security/references/hardening-checklist.md",
    "coolify-security/references/ufw-docker-guide.md",
    "coolify-troubleshoot/references/common-errors.md",
)

GATED_REFERENCES = (
    "coolify-cicd/references/api-reference.md",
    "coolify-cicd/references/gitlab-ci-pattern.md",
    "coolify-deploy/references/registry-patterns.md",
    "coolify-infrastructure/references/multi-server-setup.md",
    "coolify-infrastructure/references/swarm-guide.md",
    "coolify-observability/references/grafana-prometheus-setup.md",
    "coolify-observability/references/log-drain-configs.md",
    "coolify-security/references/hardening-checklist.md",
    "coolify-security/references/ufw-docker-guide.md",
)


def read_skill(name: str) -> str:
    entrypoint = SKILLS_ROOT / name / "SKILL.md"
    text = entrypoint.read_text(encoding="utf-8")
    operations = entrypoint.parent / "references" / "operations.md"
    if operations.exists():
        assert "references/operations.md" in text
        text += "\n" + operations.read_text(encoding="utf-8")
    return text


def test_all_task_routes_are_present_and_lean() -> None:
    assert {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()} >= REQUIRED_SKILLS
    for name in REQUIRED_SKILLS:
        assert len((SKILLS_ROOT / name / "SKILL.md").read_text(encoding="utf-8").splitlines()) < 500


def test_current_deploy_and_cli_contracts_are_used() -> None:
    actions = read_skill("coolify-actions")
    deploy = read_skill("coolify-deploy")
    cicd = read_skill("coolify-cicd")
    combined = "\n".join(
        ((PACKAGE_ROOT / "README.md").read_text(encoding="utf-8"), actions, deploy, cicd)
    )

    assert "coolify deploy uuid <APP_UUID>" in actions
    assert "/api/v1/deploy?uuid=<APP_UUID>" in cicd
    assert "/api/v1/applications/<APP_UUID>/deploy" not in combined
    assert "Railpack" in deploy and "Git-based" in deploy and "Beta" in deploy


def test_live_mutations_have_an_explicit_acceptance_gate() -> None:
    for name in ("coolify-actions", "coolify-cicd", "coolify-databases", "coolify-deploy", "coolify-security"):
        text = read_skill(name)
        assert "exact instance" in text
        assert "user acceptance" in text or "explicit acceptance" in text


def test_quick_paths_do_not_echo_secrets_or_use_unsafe_shortcuts() -> None:
    linter = (PACKAGE_ROOT / "scripts" / "lint-dockerfile.py").read_text(encoding="utf-8")
    security = read_skill("coolify-security")
    infrastructure = read_skill("coolify-infrastructure")
    observability = read_skill("coolify-observability")

    assert "{stripped_value" not in linter
    assert "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash" not in infrastructure
    assert "rm -rf /data/coolify/*" not in infrastructure
    assert "raw/master/ufw-docker" not in security
    assert "image: gcr.io/cadvisor/cadvisor:latest" not in observability


def test_changing_inventories_are_checked_at_use_time() -> None:
    databases = read_skill("coolify-databases")
    security = read_skill("coolify-security")
    assert "check the instance" in databases.lower()
    assert "check the instance" in security.lower()


def test_current_routes_and_response_parsing_cover_changed_docs() -> None:
    texts = {name: read_skill(name) for name in CHANGED_SKILLS}
    references = {
        path: (SKILLS_ROOT / path).read_text(encoding="utf-8")
        for path in DIRECTLY_LINKED_REFERENCES
    }
    combined = "\n".join((*texts.values(), *references.values()))

    assert "/api/v1/deployments/applications/{uuid}" in texts["coolify-cicd"]
    assert "/api/v1/deployments/<DEPLOYMENT_UUID>" in texts["coolify-cicd"]
    assert "/api/v1/applications/{uuid}/deployments" not in combined
    assert "/api/v1/applications/${APP_UUID}/deployments/" not in combined
    assert ".deployments[0].deployment_uuid" in references["coolify-cicd/references/api-reference.md"]
    assert ".deployments[0].deployment_uuid" in references["coolify-cicd/references/gitlab-ci-pattern.md"]


def test_live_write_examples_are_gated_and_fail_closed() -> None:
    gated = {
        name: read_skill(name)
        for name in ("coolify-cicd", "coolify-deploy", "coolify-infrastructure", "coolify-observability")
    }
    registry = (SKILLS_ROOT / "coolify-deploy" / "references" / "registry-patterns.md").read_text(encoding="utf-8")
    combined = "\n".join((*gated.values(), registry))

    for path in GATED_REFERENCES:
        text = (SKILLS_ROOT / path).read_text(encoding="utf-8")
        assert "exact instance" in text
        assert "user acceptance" in text
        assert "protected environment" in text or "manual approval" in text

    for text in (*gated.values(), registry):
        assert "exact instance" in text
        assert "user acceptance" in text
        assert "protected environment" in text or "manual approval" in text

    assert '"docker_registry_image_tag"' in combined
    assert "--fail --show-error" in combined
    rollback = read_skill("coolify-deploy").split("### Rollbacks", 1)[1].split("## Pre-Built", 1)[0]
    assert "set -e" in rollback or "&&" in rollback or "status" in rollback
    assert "--request PATCH" in rollback
    assert "/api/v1/deploy?uuid=<APP_UUID>" in rollback
    assert "restart" not in rollback


def test_tests_then_deploy_has_a_protected_production_gate() -> None:
    cicd = read_skill("coolify-cicd")
    workflow = cicd.split("### Deploy After Tests Pass", 1)[1].split("### Multi-Environment", 1)[0]
    assert "needs: test" in workflow
    assert "environment: production" in workflow or "when: manual" in workflow
    assert "protected environment" in workflow or "required reviewers" in workflow or "manual approval" in workflow


def test_webhooks_cli_installer_and_ufw_contracts_are_current() -> None:
    status = read_skill("coolify-status")
    troubleshoot = read_skill("coolify-troubleshoot")
    common_errors = (SKILLS_ROOT / "coolify-troubleshoot" / "references" / "common-errors.md").read_text(encoding="utf-8")
    security = read_skill("coolify-security")
    ufw = (SKILLS_ROOT / "coolify-security" / "references" / "ufw-docker-guide.md").read_text(encoding="utf-8")
    hardening = (SKILLS_ROOT / "coolify-security" / "references" / "hardening-checklist.md").read_text(encoding="utf-8")
    webhook = read_skill("coolify-cicd")

    assert "coolify resource list" in status
    assert "coolify deploy list" in status
    assert "then run `coolify status`" not in status
    assert "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash" not in troubleshoot + common_errors
    assert "docker system df" in common_errors
    assert "docker volume ls" in common_errors
    assert "exact named targets" in common_errors
    assert "backup/recovery evidence" in common_errors
    assert "user acceptance" in common_errors
    for unsafe_cleanup in ("docker system prune", "docker volume prune", "--volumes"):
        assert unsafe_cleanup not in common_errors
    assert "Authorization: Bearer" in webhook
    assert "token=" not in webhook.split("## Deploy Webhook URL", 1)[1].split("## GitHub Actions", 1)[0]
    for text in (security, ufw, hardening):
        assert "EXPECTED_SHA256" in text
        assert "ACTUAL_SHA256" in text
        assert "<VERSION>" not in text


def test_readme_uses_current_navigation_labels() -> None:
    readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Skills" in readme
    assert "## What is included" not in readme


if __name__ == "__main__":
    test_all_task_routes_are_present_and_lean()
    test_current_deploy_and_cli_contracts_are_used()
    test_live_mutations_have_an_explicit_acceptance_gate()
    test_quick_paths_do_not_echo_secrets_or_use_unsafe_shortcuts()
    test_changing_inventories_are_checked_at_use_time()
    test_current_routes_and_response_parsing_cover_changed_docs()
    test_live_write_examples_are_gated_and_fail_closed()
    test_tests_then_deploy_has_a_protected_production_gate()
    test_webhooks_cli_installer_and_ufw_contracts_are_current()
    test_readme_uses_current_navigation_labels()
    print("10 focused plugin contract tests passed")
