# Registry-Based Deployment Patterns

## Production gate

Before a registry push, application PATCH, or deploy, confirm the exact instance, application UUID, image tag, action, and expected effect. Require user acceptance. In CI, protect these steps with a protected environment or manual approval, and stop when approval is missing.

## GHCR (GitHub Container Registry)

### Setup in Coolify

1. Navigate to **Settings → Docker Registries → Add**
2. Configure:
   - **Registry URL**: `ghcr.io`
   - **Username**: Your GitHub username or org name
   - **Password/Token**: A GitHub PAT with `read:packages` scope (and `write:packages` if Coolify pushes images)

### Application Configuration

1. Create a new application → **Build Pack: Docker Image**
2. Set **Image**: `ghcr.io/<OWNER>/<REPO>:<TAG>`
3. Deploy triggers via webhook or API (see coolify-cicd skill)

### Complete CI/CD Workflow (Build in GitHub Actions, Deploy from GHCR)

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy
on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to GHCR
        uses: docker/login-action@v3
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

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production  # Protected environment with required reviewers.
    steps:
      - name: Trigger Coolify Deploy
        run: |
          curl --fail --show-error -X POST "${{ secrets.COOLIFY_WEBHOOK_URL }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}" \
            -H "Content-Type: application/json"
```

### Pinning vs Latest

**Floating-tag pattern** (for staging/dev):
- Set image to `ghcr.io/org/app:<STAGING_TAG>`
- Configure webhook to trigger deploy on push
- Coolify pulls the selected floating tag on each deploy

**Pinned tag pattern** (for production):
- Set image to `ghcr.io/org/app:v1.2.3`
- Update the tag in Coolify when ready to release
- Or use API to update and deploy: 
  ```bash
          curl --fail --show-error --request PATCH "https://<COOLIFY>/api/v1/applications/<UUID>" \
    -H "Authorization: Bearer <TOKEN>" \
    -d '{"docker_registry_image_tag": "v1.2.4"}'
  ```

## Docker Hub

### Setup in Coolify

1. **Settings → Docker Registries → Add**
2. Configure:
   - **Registry URL**: `docker.io` (or leave empty for Docker Hub default)
   - **Username**: Docker Hub username
   - **Password/Token**: Docker Hub access token (create at hub.docker.com → Account Settings → Security)

### Public Images

For public images, no registry configuration needed:
- Set image to `nginx:alpine`, `postgres:16`, etc.
- Coolify pulls directly without authentication

### Private Images

Register the Docker Hub credentials first, then:
- Set image to `dockerhubuser/private-app:<STAGING_TAG>`
- Coolify uses stored credentials to pull

## Private/Self-Hosted Registry

### Setup

1. **Settings → Docker Registries → Add**
2. Configure:
   - **Registry URL**: `registry.example.com` (or `registry.example.com:5000`)
   - **Username**: Registry username
   - **Password/Token**: Registry password or token

### SSL Requirements

- Registry must serve over HTTPS for Coolify to pull from it
- For self-signed certificates, configure Docker on the Coolify server to trust the CA:
  ```bash
  # On the Coolify server
  mkdir -p /etc/docker/certs.d/registry.example.com
  cp ca.crt /etc/docker/certs.d/registry.example.com/
  systemctl restart docker
  ```

### Multi-Server Requirement

When deploying the same app to multiple servers, a Docker Registry is **required** because:
1. The image is built once (on the build server or in CI)
2. Pushed to the registry
3. Each deployment server pulls the image from the registry
4. Without a registry, the image only exists on the build server

## Image Tag Update Behavior

| Scenario | Coolify Behavior |
|----------|-----------------|
| Deploy with a floating tag | Always pulls the selected tag on deploy (no caching across deploys) |
| Deploy with specific tag (`:v1.2.3`) | Pulls if not already present locally |
| Same tag, different digest | Coolify detects digest change and pulls new image |
| Webhook trigger | Pulls and deploys regardless of tag |
| Manual deploy from UI | Pulls and deploys the configured tag |

## Worked Example: Full GHCR Pipeline

### Scenario
Node.js app in a monorepo at `apps/api/`, building in GitHub Actions, deploying to Coolify via GHCR.

### Step 1: Create Dockerfile

```dockerfile
# apps/api/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
EXPOSE 3000
USER node
CMD ["node", "dist/server.js"]
```

### Step 2: GitHub Actions Workflow

```yaml
name: Deploy API
on:
  push:
    branches: [main]
    paths: ['apps/api/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Protected environment with required reviewers.
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: docker/build-push-action@v5
        with:
          context: apps/api
          push: true
          tags: ghcr.io/${{ github.repository }}/api:${{ github.sha }}
      
      - name: Deploy to Coolify
        run: |
          # Update image tag and trigger deploy
          curl --fail --show-error --request PATCH "${{ secrets.COOLIFY_URL }}/api/v1/applications/${{ secrets.COOLIFY_APP_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"docker_registry_image_tag": "${{ github.sha }}"}'
          
          curl --fail --silent --show-error "${{ secrets.COOLIFY_URL }}/api/v1/deploy?uuid=${{ secrets.COOLIFY_APP_UUID }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}"
```

### Step 3: Configure Coolify

1. Add GHCR registry (Settings → Docker Registries)
2. Create application with **Docker Image** build pack
3. Set image: `ghcr.io/<ORG>/<REPO>/api:<IMMUTABLE_TAG>`
4. Configure runtime env vars (DATABASE_URL, etc.)
5. Set health check path: `/api/health`
6. Enable the application domain and SSL

### Step 4: Verify

```bash
# Check deployment status
curl --fail --show-error --silent "https://<COOLIFY>/api/v1/deployments/applications/<UUID>" \
  -H "Authorization: Bearer <TOKEN>" | jq '.deployments[0].status'

# Check app is responding
curl -s "https://api.example.com/api/health"
```
