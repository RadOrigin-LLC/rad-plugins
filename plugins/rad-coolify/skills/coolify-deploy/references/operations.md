# coolify-deploy operations

Read the matching section only. The entrypoint's scope and approval rules still apply. Paths in these examples are relative to the skill directory unless stated otherwise.

## Build Pack Selection Decision Tree

```
START: What are you deploying?
│
├─ Multi-container app (needs multiple services)?
│  └─► Docker Compose
│      Trigger: docker-compose.yml or compose.yml exists at repo root
│
├─ Have a Dockerfile already?
│  └─► Dockerfile build pack
│      Trigger: Dockerfile present, or custom build process needed
│
├─ Deploying a pre-built image from a registry?
│  └─► Pre-built Image (Docker Image)
│      Trigger: Image already built in CI, deploying from GHCR/DockerHub/private registry
│
├─ Static site (HTML/CSS/JS only, no server needed)?
│  └─► Static build pack
│      Trigger: Purely static output, no backend, SPA or marketing site
│      Note: Use Nixpacks instead if the framework has its own build step (Next.js static export, Astro SSG)
│
├─ Standard app (single process, common language)?
│  └─► Nixpacks (default)
│      Trigger: package.json, requirements.txt, Gemfile, go.mod, Cargo.toml, etc.
│      Nixpacks auto-detects language and builds accordingly
│
└─ None of the above?
   └─► Write a Dockerfile manually
       Nixpacks detection may fail for uncommon stacks, polyglot repos, or custom runtimes
```

### Nixpacks Detection Signals

Nixpacks determines the build plan from files at the repo root (or configured base directory):

| File | Detected As | Runtime |
|------|-------------|---------|
| `package.json` | Node.js | Node LTS |
| `requirements.txt` / `pyproject.toml` / `Pipfile` | Python | Python 3.x |
| `Gemfile` | Ruby | Ruby latest |
| `go.mod` | Go | Go latest |
| `Cargo.toml` | Rust | Rust stable |
| `composer.json` | PHP | PHP 8.x |
| `mix.exs` | Elixir | Elixir latest |
| `pom.xml` / `build.gradle` | Java | JDK 17+ |
| `.swift` files | Swift | Swift latest |
| `*.csproj` | .NET | .NET 8+ |

### Railpack (Git-only Beta)

Coolify documents Railpack as a Beta build pack. It works only with Git-based deployments. Before using it, confirm that Railpack appears in the exact instance's build-pack selector and check the current Coolify guide.

Use the same repository and base-directory checks as Nixpacks. Test the generated image and application behavior before replacing a production build. Use a Dockerfile when the repository needs deterministic image instructions beyond the available automatic builders.

### Reverse Proxy: Traefik (default) vs Caddy (experimental alternative)

Coolify ships **Traefik** as the default reverse proxy. Caddy is an experimental alternative. Check the exact instance before selecting a proxy.

**Use Traefik (default) unless:**
- You specifically want Caddy's automatic HTTPS / on-the-fly cert provisioning model
- You want DNS challenge support that's simpler than Traefik's

**Switching proxies has caveats:** existing resources may need label migration. Caddy is experimental, so test the change on the exact instance before production use.

The troubleshooting flows in `coolify-troubleshoot/SKILL.md` are written against Traefik. Caddy users should consult the Caddy section of Coolify docs for proxy-specific debugging.

## Deployment Configuration

### Key Configuration Fields

| Field | Purpose | Default |
|-------|---------|---------|
| **Build Pack** | Nixpacks / Dockerfile / Docker Compose / Docker Image / Static | Auto-detected |
| **Base Directory** | Subdirectory containing the app (for monorepos) | `/` (repo root) |
| **Build Command** | Override the build step | Auto-detected by Nixpacks |
| **Install Command** | Override dependency installation | Auto-detected |
| **Start Command** | Override the process start command | Auto-detected |
| **Watch Paths** | Paths that trigger rebuild on change (webhook mode) | Entire repo |
| **Port** | Port the app listens on inside the container | `3000` |
| **Health Check Path** | HTTP path for health verification | `/` (if health check enabled) |
| **Dockerfile Location** | Path to Dockerfile (if using Dockerfile build pack) | `Dockerfile` |
| **Docker Compose Location** | Path to compose file | `docker-compose.yml` |

### Build-Time vs Runtime Environment Variables

Coolify separates environment variables into two scopes:

- **Build-time**: Available during `docker build` (injected as `ARG`). Use for: npm tokens, build flags, API keys needed at compile time.
- **Runtime**: Available when the container runs (injected as `ENV`). Use for: database URLs, API keys, secrets the running app needs.

**Common mistakes**:
1. Putting a runtime-only secret as build-time — it gets baked into the image layer and is visible via `docker history`
2. Forgetting that Nixpacks build-time vars require the `NIXPACKS_` prefix for build configuration overrides
3. Not realizing that build-time variables appear in build logs by default

### NIXPACKS_* Override System

Force specific runtimes, versions, or commands via `NIXPACKS_*` environment variables (e.g., `NIXPACKS_NODE_VERSION=20`, `NIXPACKS_BUILD_CMD`, `NIXPACKS_PKGS`). See `references/build-packs.md` for the full variable table and `nixpacks.toml` configuration.

### Monorepo Pattern

For monorepos where only one subdirectory should build:

1. Set **Base Directory** to the app's subdirectory (e.g., `apps/web`)
2. Nixpacks will look for `package.json` (or equivalent) in that subdirectory
3. If using Dockerfile, set **Dockerfile Location** relative to repo root
4. Set **Watch Paths** to the subdirectory to avoid rebuilds on unrelated changes
5. Build context is the repo root; base directory controls where Nixpacks looks for the app

### Pre/Post Deployment Scripts

Execute custom scripts before or after the main deployment:

- **Pre-deployment**: Run database migrations, warm caches, notify services. Executes before the new container receives traffic.
- **Post-deployment**: Clean up old resources, send notifications, update external registries. Executes after successful deployment.

Configure in the application settings under the deployment section. Scripts run in the container context.

## Rolling Deployments and Rollbacks

> **Honest framing on "zero-downtime."** Coolify's rolling deploy gives effectively-zero-downtime **only when all of these conditions hold**: single-container deployment (NOT docker-compose), no exclusive host port bindings, healthcheck configured and passing reliably, persistent volumes either absent or attachable to multiple containers simultaneously. When any condition fails, Coolify falls back to a recreate strategy (brief downtime). Verify the conditions and watch the deployment metric on the exact instance before making an availability claim.

### Rolling Deployment Flow

1. New container is built and started alongside the old one
2. Coolify runs health checks against the new container
3. If health check passes → Traefik routes traffic to new container, old container is stopped and removed
4. If health check fails → New container is stopped, old container keeps serving traffic, deployment marked as failed

**Health check configuration**: Set a health check path (e.g., `/healthz` or `/api/health`). Coolify uses HTTP health checks — the endpoint must return a 2xx status. **The endpoint should check actual dependencies** (DB connection, cache reachability) — a healthcheck that just returns `200 OK` regardless of state defeats the purpose.

### When Rolling Deploy Does NOT Apply

Coolify falls back to **recreate** strategy (stop old, start new — brief downtime) when:

- The application uses persistent volumes that cannot be mounted on two containers simultaneously
- Docker Compose deployments (managed by Docker Compose lifecycle, not Coolify's rolling logic)
- Health checks are not configured (no way to verify new container is ready)
- The container requires exclusive port binding on the host (not through Traefik)
- Swarm mode deployments (use Swarm's own rolling update mechanism and inspect old container cleanup on the exact instance)

### Rollbacks

**Via UI**: Navigate to the application → Deployments tab → click the "Rollback" button on any previous successful deployment. This redeploys the image/commit from that deployment.

**Via API**:
```bash
set -e

curl --fail --show-error --request PATCH "https://<COOLIFY_FQDN>/api/v1/applications/<APP_UUID>" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"docker_registry_image_tag": "<PREVIOUS_IMAGE_TAG>"}'

curl --fail --show-error \
  "https://<COOLIFY_FQDN>/api/v1/deploy?uuid=<APP_UUID>" \
  -H "Authorization: Bearer <YOUR_API_TOKEN>"
```

**Persistent storage**: Volumes are preserved across deployments. Define volumes in the application's storage settings to persist data between deploys (database files, uploads, etc.).

## Pre-Built Image Deployment (Registry Pattern)

### Workflow

1. **Configure a Docker Registry** in Coolify (Settings → Docker Registries) — provide registry URL, username, and password/token
2. **Create an application** → choose "Docker Image" as the build pack
3. **Set the image** field to the full image reference, using an immutable tag or digest: `ghcr.io/org/app:<IMMUTABLE_TAG>` or `registry.example.com/app@sha256:<DIGEST>`
4. **Deploy** — Coolify pulls the image from the registry and runs it

### Image Tag Behavior

- Coolify pulls the image on every deploy (does not cache across deploys)
- Use an immutable tag or digest for controlled deployments
- Treat floating tags as a deliberate staging choice and record the trigger that refreshes them

### Private Registry Authentication

Credentials are stored in Coolify's encrypted database. Configure once per registry:
- **GHCR**: Use a GitHub Personal Access Token (PAT) with `read:packages` scope
- **Docker Hub**: Use a Docker Hub access token
- **Custom Registry**: Provide username and password/token for your registry
