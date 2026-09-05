# coolify-cicd operations

Read the matching section only. The entrypoint's scope and approval rules still apply. Paths in these examples are relative to the skill directory unless stated otherwise.

## Deployment Trigger Methods

| Method | Best For | Complexity |
|--------|----------|------------|
| **Git Push (Auto-deploy)** | Simple projects, Coolify builds from source | Lowest |
| **Deploy Webhook URL** | Quick integration, no API token needed | Low |
| **REST API** | Full control, multi-step pipelines | Medium |
| **GitHub Actions + API** | Enterprise CI/CD with tests before deploy | Medium |
| **GHCR + API** | Build externally, deploy pre-built images | Higher |

Choose based on your build pipeline: if Coolify builds from source, use Git Push or Webhook. If CI builds the image, use GHCR + API. If neither fits, use the REST API directly for full control.

## REST API

### Authentication

All API requests require a Bearer token:
```bash
curl -H "Authorization: Bearer <YOUR_API_TOKEN>" \
     "https://<COOLIFY_FQDN>/api/v1/..."
```

Generate tokens in **Coolify UI → Security → API Tokens**. Tokens are team-scoped — they grant access to all resources within the team.

### Core Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/applications` | List all applications |
| `GET` | `/api/v1/applications/{uuid}` | Get application details |
| `PATCH` | `/api/v1/applications/{uuid}` | Update application settings |
| `GET` or `POST` | `/api/v1/deploy` | Trigger deployment by `uuid`, `tag`, `force`, or `pr` |
| `POST` | `/api/v1/applications/{uuid}/restart` | Restart application |
| `POST` | `/api/v1/applications/{uuid}/stop` | Stop application |
| `GET` | `/api/v1/deployments/applications/{uuid}` | List deployments |
| `GET` | `/api/v1/servers` | List servers |
| `GET` | `/api/v1/teams` | List teams |
| `GET` | `/api/v1/projects` | List projects |

### Trigger a Deployment

```bash
# Basic deploy (GET is the documented form)
curl --fail --show-error \
  "https://<COOLIFY_FQDN>/api/v1/deploy?uuid=<APP_UUID>" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"

# With optional parameters
curl --fail --show-error \
  "https://<COOLIFY_FQDN>/api/v1/deploy?uuid=<APP_UUID>&force=true" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"

# Response (async — returns deployment job)
{
  "deployments": [
    {
      "message": "Deployment request queued.",
      "resource_uuid": "app-xxxx",
      "deployment_uuid": "dep-xxxx-xxxx"
    }
  ]
}
```

**Parameters**: `uuid` (resource UUID, comma-separated for batch), `tag` (tag name), `force` (boolean, skip cache), `pr` (PR number for preview deploys).

### Check Deployment Status

```bash
curl --fail --show-error --silent "https://<COOLIFY_FQDN>/api/v1/deployments/<DEPLOYMENT_UUID>" \
  -H "Authorization: Bearer <TOKEN>" | jq '.status'

# Status values: queued, in_progress, finished, failed, cancelled
```

### Get Application Logs

```bash
curl -s "https://<COOLIFY_FQDN>/api/v1/applications/<APP_UUID>/logs?lines=100" \
  -H "Authorization: Bearer <TOKEN>"
```

### Update Application Settings

```bash
# Update image tag for pre-built image deployments
curl --fail --show-error --request PATCH "https://<COOLIFY_FQDN>/api/v1/applications/<APP_UUID>" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "docker_registry_image_tag": "v1.2.3"
  }'
```

## Deploy Webhook URL

Each application has a unique webhook URL (found in **Application → Webhooks** tab):

```
https://<COOLIFY_FQDN>/api/v1/deploy?uuid=<APP_UUID>
```

**Method:** GET is the canonical method in Coolify's own docs and GitHub Actions examples. POST also works (with the uuid/tag in the JSON body). The URL carries the resource UUID only. Send the API token in the `Authorization: Bearer <TOKEN>` header. Do not put a token in the URL query string.

```bash
# Canonical (GET)
curl --fail --show-error \
  "https://<COOLIFY_FQDN>/api/v1/deploy?uuid=<APP_UUID>" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"

# POST is also documented when the values are sent as JSON.
curl --fail --show-error -X POST \
  "https://<COOLIFY_FQDN>/api/v1/deploy" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"uuid": "<APP_UUID>"}'
```

**Always use `--fail`** (or `--fail-with-body` for visibility) — without it, curl returns exit 0 even when the deploy endpoint errors, and CI passes despite a failed trigger. This is exactly what `scripts/audit-cicd.py` checks for.

**Webhook vs API:** The webhook URL is simpler (single curl call), but offers less control. Use the full API for updating settings before deploy, checking status afterward, or complex multi-step workflows. The bundled `@radoriginllc/coolify-mcp` server wraps the full API and is preferable for any non-trivial CI/CD flow.

## GitHub Actions Integration

### Basic Deploy on Push

```yaml
name: Deploy to Coolify
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Configure required reviewers in this protected environment.
    steps:
      - name: Trigger Coolify Deployment
        run: |
          curl --request GET \
            "${{ secrets.COOLIFY_WEBHOOK }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}" \
            --fail --silent --show-error
```

### Required GitHub Secrets

| Secret | Value | Example |
|--------|-------|---------|
| `COOLIFY_WEBHOOK` | Deploy webhook URL from app's Webhook page | `https://coolify.example.com/api/v1/deploy?uuid=app-xxxx` |
| `COOLIFY_API_TOKEN` | API token from Keys & Tokens → API Tokens | `token with "Deploy" permission` |
| `COOLIFY_URL` | Coolify instance URL (for API calls) | `https://coolify.example.com` |

### Deploy After Tests Pass

```yaml
name: Test and Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test

  deploy:
    needs: test    # Only runs if tests pass
    runs-on: ubuntu-latest
    environment: production  # Protected environment with required reviewers.
    steps:
      - name: Deploy to Coolify
        run: |
          curl --fail --silent --show-error \
            "${{ secrets.COOLIFY_URL }}/api/v1/deploy?uuid=${{ secrets.COOLIFY_APP_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}"
```

### Multi-Environment (Staging + Production)

```yaml
name: Deploy Pipeline
on:
  push:
    branches: [main, develop]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          curl --fail --silent --show-error \
            "${{ secrets.COOLIFY_URL }}/api/v1/deploy?uuid=${{ secrets.COOLIFY_STAGING_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}"

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production    # Protected environment with required reviewers.
    steps:
      - name: Deploy to Production
        run: |
          curl --fail --silent --show-error \
            "${{ secrets.COOLIFY_URL }}/api/v1/deploy?uuid=${{ secrets.COOLIFY_PROD_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}"
```

## GHCR Pattern (Full Pipeline)

Build in GitHub Actions → push to GHCR → trigger Coolify to deploy the image:

```yaml
name: Build, Push, Deploy
on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-push-deploy:
    runs-on: ubuntu-latest
    environment: production  # Protected environment; stop unless a reviewer approves.
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Update image tag in Coolify
        run: |
          curl --fail --show-error --request PATCH \
            "${{ secrets.COOLIFY_URL }}/api/v1/applications/${{ secrets.COOLIFY_APP_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"docker_registry_image_tag": "${{ github.sha }}"}'

      - name: Trigger deployment
        run: |
          curl --fail --silent --show-error \
            "${{ secrets.COOLIFY_URL }}/api/v1/deploy?uuid=${{ secrets.COOLIFY_APP_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}"
```

## Webhooks and Auto-Deploy

### Git Provider Webhooks

Coolify can auto-deploy when it detects a push to the configured branch:

1. **Application → General → Git Repository** — configure the repo and branch
2. Enable **Auto Deploy** — Coolify registers a webhook with the git provider
3. On push to the configured branch, Coolify triggers a build and deploy automatically

### Branch-Specific Rules

- Each Coolify application is configured for one branch
- For multiple branches (staging, production), create separate Coolify applications pointing to different branches
- Use the same repo, different branch configuration per application

### PR Preview Environments

Coolify supports preview deployments for pull requests:

1. Enable **Preview Deployments** in the application settings
2. When a PR is opened against the configured branch, Coolify creates a temporary deployment
3. The preview gets its own subdomain (e.g., `pr-123.preview.example.com`)
4. When the PR is merged or closed, the preview environment is automatically destroyed

**Limitations**:
- Preview environments share the server resources with production
- Each preview creates a new container (resource-heavy for many concurrent PRs)
- Database-dependent apps need a strategy for preview databases
- Environment variables are inherited from the main application
