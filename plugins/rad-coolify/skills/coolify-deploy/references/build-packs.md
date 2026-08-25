# Build Packs — Detailed Reference

> Build-pack availability changes. Check the exact instance's build-pack selector and the current [Coolify build-pack documentation](https://coolify.io/docs/applications/build-packs) before choosing a pack. Railpack is a Git-only Beta build pack.

> **Important: Nixpacks is in maintenance mode.** Practical impact for Coolify users: newer runtime versions may not be available in Nixpacks. Switch to a Dockerfile build pack when the required runtime is unavailable. Existing pinned-version overrides can continue to work for supported versions.

## Nixpacks Deep Dive

### How Detection Works

Nixpacks scans files in the configured base directory (default: repo root) in a priority order. The first match wins:

1. Check for `Procfile` → Use detected language + Procfile start command
2. Check for language-specific lock files (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb`)
3. Check for project manifest files (`package.json`, `requirements.txt`, `go.mod`, etc.)
4. Check for source file extensions as fallback (`.py`, `.rb`, `.go`, etc.)

### Nixpacks Build Phases

Every Nixpacks build follows four phases:

1. **Setup** — Install system dependencies (Nix packages)
2. **Install** — Install language-level dependencies (`npm install`, `pip install`, etc.)
3. **Build** — Run the build command (`npm run build`, `cargo build --release`, etc.)
4. **Start** — Define the process start command

Override any phase with `NIXPACKS_*` environment variables or a `nixpacks.toml` file.

### NIXPACKS_* Environment Variable Overrides

| Variable | Example | Effect |
|----------|---------|--------|
| `NIXPACKS_NODE_VERSION` | `20` | Force Node.js 20 |
| `NIXPACKS_PYTHON_VERSION` | `3.12` | Force Python 3.12 |
| `NIXPACKS_INSTALL_CMD` | `pnpm install --frozen-lockfile` | Override install command |
| `NIXPACKS_BUILD_CMD` | `npm run build:prod` | Override build command |
| `NIXPACKS_START_CMD` | `node dist/server.js` | Override start command |
| `NIXPACKS_PKGS` | `ffmpeg imagemagick` | Add system packages |
| `NIXPACKS_APT_PKGS` | `libvips-dev` | Add apt packages |

### nixpacks.toml Configuration

Place at repo root (or base directory) for fine-grained control:

```toml
[phases.setup]
nixPkgs = ["ffmpeg", "imagemagick"]
aptPkgs = ["libvips-dev"]

[phases.install]
cmds = ["pnpm install --frozen-lockfile"]

[phases.build]
cmds = ["pnpm run build"]

[start]
cmd = "node dist/server.js"
```

### Monorepo Failure Modes

Nixpacks detection fails on monorepos when:

| Failure Mode | Cause | Fix |
|-------------|-------|-----|
| Wrong app detected | Multiple `package.json` files; Nixpacks picks root | Set **Base Directory** to the correct subdirectory |
| Build fails with missing deps | Root `package.json` doesn't have the app's dependencies | Set base directory; or use workspace-aware install command |
| Wrong start command | Nixpacks infers from root, not the target app | Set `NIXPACKS_START_CMD` explicitly |
| Turborepo/Nx confusion | Monorepo tools have their own build orchestration | Use a Dockerfile for complex monorepo builds |
| Workspace hoisting issues | pnpm/yarn workspaces hoist differently | Set install command: `pnpm install --filter=app-name...` |

### Node.js Specifics

```
# Force specific Node version
NIXPACKS_NODE_VERSION=20

# Use pnpm
NIXPACKS_INSTALL_CMD=pnpm install --frozen-lockfile
NIXPACKS_BUILD_CMD=pnpm run build

# Add system packages needed for native modules
NIXPACKS_PKGS=python3 make gcc

# Set memory for build (if OOM during build)
NODE_OPTIONS=--max-old-space-size=4096
```

### Python Specifics

```
# Force Python version
NIXPACKS_PYTHON_VERSION=3.12

# Use poetry
NIXPACKS_INSTALL_CMD=pip install poetry && poetry install --no-dev
NIXPACKS_BUILD_CMD=poetry run python manage.py collectstatic --noinput

# Django-specific
NIXPACKS_START_CMD=gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
```

### Go Specifics

```
# Build with specific flags
NIXPACKS_BUILD_CMD=go build -ldflags="-s -w" -o /app/server ./cmd/server

# Start command
NIXPACKS_START_CMD=/app/server
```

## Dockerfile Build Pack

### When to Use Dockerfile Over Nixpacks

- Multi-stage builds needed for optimization
- Custom system dependencies that Nixpacks cannot resolve
- Specific base image requirements (Alpine, Distroless, etc.)
- Complex monorepo builds with custom dependency resolution
- Apps requiring build-time secrets injected via `--mount=type=secret`
- Polyglot applications not detectable by Nixpacks
- When you need deterministic, reproducible builds

### Best Practices for Coolify Dockerfiles

```dockerfile
# Multi-stage build pattern
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --production=false
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./
USER nextjs
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

**Key points for Coolify compatibility:**

1. **EXPOSE the correct port** — Coolify reads the `EXPOSE` directive to know which port to route to. Override in Coolify settings if needed.
2. **Use non-root user** — Security best practice; Coolify does not enforce this but should.
3. **Keep final image small** — Multi-stage builds avoid shipping build tools in production.
4. **No hardcoded secrets** — Use build args or mounted secrets for build-time values.

### Build Secrets in Dockerfile

```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
```

Configure the secret name in Coolify's Build Secrets section (not regular environment variables).

## Docker Compose Build Pack

### When to Use

- Multi-container applications (app + worker + Redis + etc.)
- Local development parity (same compose file works locally and in Coolify)
- Complex networking between services
- Volume sharing between containers

### Coolify-Specific Compose Behavior

- Coolify manages the `docker-compose up` lifecycle
- Traefik labels on the main web service control routing
- Other services in the compose file are accessible via their service name on the internal network
- Health checks defined in compose are respected
- Environment variables from Coolify are injected into all services (or targeted via `environment` in compose)

### Example Compose for Coolify

```yaml
version: "3.8"
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3
  
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: node dist/worker.js
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## Static Build Pack

### When to Use

- Pure HTML/CSS/JS sites with no build step
- Pre-built SPA bundles (output from a build pipeline)
- Simple marketing or documentation sites

### When NOT to Use

- Framework sites that need a build step (Next.js, Astro, Nuxt) → Use Nixpacks
- Sites that need a server for SSR → Use Nixpacks or Dockerfile
- API backends → Use Nixpacks or Dockerfile

### Configuration

Coolify serves static files via a built-in web server. Configure:
- **Publish Directory**: The directory containing the static files (e.g., `dist`, `build`, `public`)
- **Custom headers**: Set caching, security headers as needed

## Railpack (Experimental)

### Current Status

Railpack is an alternative to Nixpacks, developed by Railway. In Coolify:
- It works only for Git-based deployments.
- It is marked Beta and must be explicitly selected.
- Feature support can change, so check the exact instance before use.
- Test the generated image in staging before production.

### Differences from Nixpacks

| Aspect | Nixpacks | Railpack |
|--------|----------|----------|
| Base tech | Nix packages | Debian-based |
| Image size | Moderate | Often smaller |
| Build speed | Good | Potentially faster |
| Language support | Very broad | Growing (focus on Node, Python, Go, Rust) |
| Maturity | Production-ready | Beta |
| Configuration | nixpacks.toml, env vars | railpack.json (limited docs) |
| Community | Large, well-documented | Small, early-stage |

### Migration from Nixpacks

1. Test in a staging environment first
2. Check that all system dependencies are available
3. Verify build output matches Nixpacks build
4. Monitor for issues for at least one release cycle before using in production

**Recommendation**: Check the current instance and test Railpack in staging before using it in production. Use Dockerfile when deterministic image instructions are required.
