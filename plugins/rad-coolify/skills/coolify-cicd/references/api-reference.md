# Coolify REST API v1 Reference

> **Honest framing on API stability.** The API is versioned at `/api/v1` but has no formal stability guarantee — Coolify itself is `v4.0.0-beta.474` (April 2026). The OpenAPI spec and actual API behavior occasionally diverge. Two known active bugs as of April 2026:
> - **Issue #7702**: `GET /api/v1/projects` is documented to return an `environments` array per project, but the actual response does not include it.
> - **Issue #8782**: `POST /api/v1/services` rejects the documented `urls` parameter with HTTP 422.
>
> **For production automation, pin to a specific Coolify version and test API calls against your instance** before building tooling on top. The `@radoriginllc/coolify-mcp` server (bundled with this plugin) wraps these endpoints — when the underlying API changes, update the MCP package rather than re-implementing the wrapper.

## Base URL

```
https://<COOLIFY_FQDN>/api/v1
```

Normal API operations use this prefix. Health is the exception: `GET /api/health` is outside `/api/v1`.

## Authorization

API requests use a Bearer API token created under **Keys & Tokens > API Tokens**. Tokens are scoped to the active team. Coolify Private Keys are SSH keys for server access or private Git deploy keys. Never use a Private Key as an API token.

Current token permissions are:

- `read`: status and ordinary resource reads
- `read:sensitive`: logs and sensitive fields
- `deploy`: deployments and deployment lifecycle controls
- `write`: application, environment, and other resource changes
- `root`: complete API control for Coolify administration

Use least privilege. Start with `read`, then add only the permission required by the task. `root` bypasses permission checks and is unnecessary for normal deployment work.

**New in beta.474 (April 2026):** Tokens now support optional **expiration dates**. For long-running CI/CD integrations, set an expiration aligned with your secret rotation policy and refresh before it elapses.

## Applications

### List Applications

```
GET /applications
```

Response:
```json
[
  {
    "uuid": "app-xxxx-xxxx",
    "name": "my-app",
    "fqdn": "https://app.example.com",
    "status": "running",
    "build_pack": "nixpacks",
    "git_repository": "github.com/org/repo",
    "git_branch": "main",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get Application

```
GET /applications/{uuid}
```

Returns full application details including environment variables, deployment settings, and current status.

### Update Application

```
PATCH /applications/{uuid}
Content-Type: application/json

{
  "name": "new-name",
  "fqdn": "https://new.example.com",
  "git_branch": "develop",
  "build_pack": "dockerfile",
  "docker_registry_image_tag": "v2.0.0",
  "ports_mappings": "3000:3000",
  "health_check_enabled": true,
  "health_check_path": "/healthz",
  "health_check_interval": 30,
  "health_check_timeout": 10,
  "health_check_retries": 3
}
```

### Deploy Application

```
GET /deploy?uuid={app_uuid}
GET /deploy?uuid={app_uuid}&force=true
GET /deploy?tag={tag_name}
GET /deploy?uuid={uuid1},{uuid2}  (batch deploy)
```

Query parameters:
- `uuid` — Resource UUID(s), comma-separated
- `tag` — Tag name(s), comma-separated
- `force` — Boolean, force rebuild without cache
- `pr` — Integer, PR number (incompatible with `tag`)

Response:
```json
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

### Restart Application

```
POST /applications/{uuid}/restart
```

### Stop Application

```
POST /applications/{uuid}/stop
```

### Start Application

```
POST /applications/{uuid}/start
```

### List Deployments

```
GET /applications/{uuid}/deployments
```

Response:
```json
[
  {
    "id": 123,
    "deployment_uuid": "dep-xxxx",
    "status": "finished",
    "commit_sha": "abc123",
    "created_at": "2024-01-15T10:30:00Z",
    "finished_at": "2024-01-15T10:32:45Z",
    "logs": "Build output..."
  }
]
```

### Get Deployment Logs

```
GET /applications/{uuid}/deployments/{deployment_uuid}
```

Returns detailed deployment information including full build logs.

## Environment Variables

### List Environment Variables

```
GET /applications/{uuid}/envs
```

Response:
```json
[
  {
    "id": 1,
    "key": "DATABASE_URL",
    "value": "postgresql://...",
    "is_build_time": false,
    "is_preview": false
  }
]
```

### Create Environment Variable

```
POST /applications/{uuid}/envs
Content-Type: application/json

{
  "key": "NEW_VAR",
  "value": "some-value",
  "is_build_time": false,
  "is_preview": false
}
```

### Update Environment Variable

```
PATCH /applications/{uuid}/envs/{id}
Content-Type: application/json

{
  "value": "updated-value"
}
```

### Delete Environment Variable

```
DELETE /applications/{uuid}/envs/{id}
```

## Servers

### List Servers

```
GET /servers
```

### Get Server

```
GET /servers/{uuid}
```

### Validate Server

```
GET /servers/{uuid}/validate
```

## Projects

### List Projects

```
GET /projects
```

### Get Project

```
GET /projects/{uuid}
```

## Teams

### List Teams

```
GET /teams
```

### Get Current Team

```
GET /teams/current
```

## Databases

### List Databases

```
GET /databases
```

### Get Database

```
GET /databases/{uuid}
```

### Start Database

```
POST /databases/{uuid}/start
```

### Stop Database

```
POST /databases/{uuid}/stop
```

### Restart Database

```
POST /databases/{uuid}/restart
```

## Services

### List Services

```
GET /services
```

### Get Service

```
GET /services/{uuid}
```

### Start Service

```
POST /services/{uuid}/start
```

### Stop Service

```
POST /services/{uuid}/stop
```

## Deploy Webhook

### Webhook Trigger

```
POST /deploy?uuid={app_uuid}&token={webhook_token}

# Or with query parameters
GET /deploy?uuid={app_uuid}&token={webhook_token}&force=true
```

The webhook token is unique per application and found in the application's webhook settings.

## Common API Patterns

### Poll for Deployment Completion

```bash
#!/bin/bash
# poll-deploy.sh — wait for deployment to finish

APP_UUID="$1"
DEPLOY_UUID="$2"
COOLIFY_URL="$3"
TOKEN="$4"

while true; do
  STATUS=$(curl -s \
    "${COOLIFY_URL}/api/v1/applications/${APP_UUID}/deployments/${DEPLOY_UUID}" \
    -H "Authorization: Bearer ${TOKEN}" | jq -r '.status')
  
  case "$STATUS" in
    "finished") echo "Deployment succeeded"; exit 0 ;;
    "failed")   echo "Deployment failed"; exit 1 ;;
    "cancelled") echo "Deployment cancelled"; exit 1 ;;
    *) echo "Status: $STATUS — waiting..."; sleep 15 ;;
  esac
done
```

### Deploy and Wait (GitHub Actions)

```yaml
- name: Deploy and wait
  run: |
    # Trigger deploy
    RESPONSE=$(curl -s -X POST \
      "${{ secrets.COOLIFY_URL }}/api/v1/applications/${{ secrets.APP_UUID }}/deploy" \
      -H "Authorization: Bearer ${{ secrets.TOKEN }}" \
      -H "Content-Type: application/json")
    
    DEPLOY_UUID=$(echo "$RESPONSE" | jq -r '.deployment_uuid')
    echo "Deployment started: $DEPLOY_UUID"
    
    # Poll for completion (max 5 minutes)
    for i in $(seq 1 20); do
      sleep 15
      STATUS=$(curl -s \
        "${{ secrets.COOLIFY_URL }}/api/v1/applications/${{ secrets.APP_UUID }}/deployments/$DEPLOY_UUID" \
        -H "Authorization: Bearer ${{ secrets.TOKEN }}" | jq -r '.status')
      
      echo "Attempt $i: $STATUS"
      
      if [ "$STATUS" = "finished" ]; then
        echo "Deploy succeeded!"
        exit 0
      elif [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
        echo "Deploy failed with status: $STATUS"
        exit 1
      fi
    done
    
    echo "Deploy timed out"
    exit 1
```

## Rate Limits

The Coolify API does not document explicit rate limits for self-hosted instances, but:
- Avoid polling more frequently than every 10-15 seconds
- Batch operations where possible
- Use webhooks for event-driven workflows instead of polling
