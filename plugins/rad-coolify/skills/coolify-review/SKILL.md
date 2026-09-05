---
name: coolify-review
description: Review a project read-only for self-hosted Coolify deployment readiness using local checks and repository evidence.
---

# Review a Coolify Deployment

Review the current project for self-hosted Coolify v4 deployment risks. Run the local validators first, then use judgment for issues that file-pattern checks cannot decide.

## Write Boundary

This skill is read-only. Do not edit project files, deploy, restart services, or change Coolify settings. Report findings and let the user choose any follow-up work.

## Resolve the Plugin Path

Use the loaded path of this `SKILL.md`. Its plugin root is two directories above the skill directory. Do not assume a fixed install path or use a client-specific environment variable.

## Procedure

1. Identify relevant project files:
   - `Dockerfile*`
   - `docker-compose*.yml`, `docker-compose*.yaml`, `compose*.yml`, and `compose*.yaml`
   - `.github/workflows/*.yml` and `.gitlab-ci.yml`
   - `nixpacks.toml`
   - `.env*` and `.dockerignore`
   - application health endpoints such as `/health` or `/healthz`

2. Run the four bundled validators against the project root. Use the active Python interpreter and continue when a validator exits `1`, because that exit code means it found issues.

```powershell
python <plugin-root>\scripts\lint-dockerfile.py <project-root> --json
python <plugin-root>\scripts\lint-compose.py <project-root> --json
python <plugin-root>\scripts\check-coolify-env.py <project-root> --json
python <plugin-root>\scripts\audit-cicd.py <project-root> --json
```

If Python is unavailable, state which checks could not run. Do not claim mechanical validation.

3. Keep the validator findings as evidence. Do not duplicate them as new judgment findings.

4. Review what the scripts cannot decide:
   - whether the health endpoint checks required dependencies;
   - whether the Docker base image and build stages fit the workload;
   - whether Compose dependencies, networks, and volumes match the application;
   - whether CI/CD separates environments and can detect a failed deployment;
   - whether build-time and runtime variables are separated;
   - whether Traefik routes and exposed ports match the intended service;
   - whether stateful services have a suitable backup plan.

5. Classify findings:
   - Critical: likely deployment failure, data loss, or secret exposure.
   - Warning: a reliability or security weakness that needs review.
   - Suggestion: an optional improvement.

6. Return one report:

```markdown
# Coolify Deployment Review

## Summary
- Critical: [count]
- Warnings: [count]
- Suggestions: [count]
- Assessment: Ready | Needs work | Not ready

## Mechanical findings
[Findings from the four scripts, with file and line evidence]

## Judgment findings
[Only issues that required repository context]

## Checks that could not run
[Missing files, tools, access, or facts]

## User choices
[Keep, fix, investigate, or accept each material issue]
```

## Limits

- File review cannot prove that a deployment will succeed.
- The validators use rules and heuristics. False positives and missed issues are possible.
- Do not run `docker build`, `docker compose up`, or live Coolify actions unless the user asks.
- Coolify v4 changes often. Verify version-specific behavior against the user's instance or current official documentation when it affects a decision.
