# Common Coolify Errors and Fixes

## Build Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `npm ERR! code ERESOLVE` | Peer dependency conflict | Set `NIXPACKS_INSTALL_CMD=npm install --legacy-peer-deps` |
| `ENOMEM` during `npm run build` | Node.js ran out of memory | Set `NODE_OPTIONS=--max-old-space-size=4096` as env var |
| `error: no matching packages found` | Nixpacks can't find a Nix package | Use `NIXPACKS_APT_PKGS` instead of `NIXPACKS_PKGS` |
| `Could not detect language` | No package.json/requirements.txt at base directory | Set base directory correctly or add the manifest file |
| `fatal: repository not found` | Git repo URL wrong or private without credentials | Check repo URL and configured Git credentials in Coolify |
| `error: Your local changes to the following files would be overwritten` | Coolify workspace has uncommitted changes | Force rebuild or check for write permissions in build directory |
| `pip: command not found` | Nixpacks didn't detect Python | Set `NIXPACKS_PYTHON_VERSION=3.12` |
| `cargo build failed` | Missing system dependencies for Rust crates | Add to `NIXPACKS_APT_PKGS`: `pkg-config libssl-dev` |
| `ModuleNotFoundError` at build time | Python deps not installed before build step | Ensure `requirements.txt` lists all dependencies |
| `sharp: Installation error` | Missing native library for sharp | Add `NIXPACKS_APT_PKGS=libvips-dev` |
| `node-gyp rebuild failed` | Missing build tools for native Node modules | Add `NIXPACKS_PKGS=python3 make gcc` |
| `pnpm: not found` | Nixpacks defaulting to npm | Set `NIXPACKS_INSTALL_CMD=corepack enable && pnpm install --frozen-lockfile` |
| `bun: not found` | Nixpacks doesn't auto-detect Bun | Set build pack to Dockerfile or use `NIXPACKS_START_CMD=bun run start` |
| `Dockerfile not found` | Dockerfile build pack selected but file missing | Check Dockerfile path in Coolify settings; default is `Dockerfile` at repo root |
| `docker-compose.yml: no such file or directory` | Compose file path wrong | Set the correct compose file path in Coolify settings |

## Runtime Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `EADDRINUSE: address already in use` | App binding to port already taken by another process | Change the app's listen port or ensure old container is stopped |
| `ECONNREFUSED` to database | Database container not running or wrong hostname | Check DB container status; use container name as hostname |
| `Error: connect ECONNREFUSED 127.0.0.1:5432` | App connecting to localhost instead of container name | Use the container name in DATABASE_URL, not localhost |
| `SSL routines: wrong version number` | Connecting with SSL to a non-SSL endpoint (or vice versa) | Check `sslmode` in connection string matches DB config |
| `too many open files` | ulimit too low | Set `ulimit -n 65536` in container or Docker daemon config |
| `DNS resolution failed` | Container can't resolve other container names | Ensure containers are on the same Docker network (`coolify`) |

## Deployment Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Deployment stuck at "In Progress" | Build process hanging (infinite loop, waiting for input) | Cancel deployment; check build command doesn't require stdin |
| "Port already allocated" | Another container using the same host port | Stop conflicting container or change port mapping |
| "No space left on device" | Disk full (Docker images, logs, or data) | Start with read-only inspection: `df -h`, `docker system df`, `docker ps -a`, and `docker volume ls`. Any cleanup needs exact named targets, backup/recovery evidence where relevant, and user acceptance. |
| "Network not found: coolify" | Docker network deleted or corrupted | `docker network create coolify`; restart Coolify |
| "Image not found" for pre-built | Registry credentials wrong or image tag doesn't exist | Verify registry config and image tag in Coolify |
| "Healthcheck failed" | App doesn't respond to health check path | Verify health check path returns 200; increase timeout |

## SSL/Certificate Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `NET::ERR_CERT_AUTHORITY_INVALID` | Self-signed cert or Let's Encrypt staging cert | Check Traefik is using production ACME server |
| `ERR_SSL_VERSION_OR_CIPHER_MISMATCH` | TLS version conflict | Update Traefik TLS minimum version or check client compatibility |
| `ERR_CERT_DATE_INVALID` | Certificate expired | Force renewal: restart `coolify-proxy` |
| `ERR_TOO_MANY_REDIRECTS` | Cloudflare Flexible SSL + Coolify HTTPS redirect | Set Cloudflare to "Full (Strict)" SSL mode |
| `acme: error: 429` | Let's Encrypt rate limit hit | Wait 1 hour; use staging for testing |
| `acme: could not determine the zone` | DNS challenge misconfigured | Verify DNS provider API credentials |

## Coolify System Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Coolify dashboard blank/white screen | Frontend build issue after update | Clear browser cache; try incognito mode; check `docker logs coolify` |
| "Database connection refused" in Coolify logs | Coolify's internal PostgreSQL is down | `docker restart coolify-db` |
| Coolify websocket disconnects | Port 6001 blocked by firewall | `ufw allow 6001/tcp` |
| "Permission denied" when connecting to server | SSH key issue between Coolify and target server | Re-add SSH key in Coolify server settings; check `~/.ssh/authorized_keys` |
| Coolify update fails mid-way | Network interruption during update | Download the exact versioned installer from the official release notes, verify its checksum or signature, inspect it, then run `/tmp/coolify-install-<VERSION>.sh` |
| Sentinel not reporting metrics | Sentinel container not running | `docker restart coolify-sentinel` |

## Docker System Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot connect to the Docker daemon` | Docker service not running | `systemctl start docker` |
| `docker: Error response from daemon: Conflict` | Container name already in use | Remove old container: `docker rm <CONTAINER>` |
| Build context too large (>1GB) | Missing or inadequate `.dockerignore` | Add `node_modules`, `.git`, `dist` to `.dockerignore` |
| `no matching manifest for linux/arm64` | Image doesn't support server architecture | Use `--platform linux/amd64` or find ARM-compatible image |
| Docker daemon OOM | Too many containers or builds consuming all RAM | Set memory limits on containers; clean up unused resources |

## Quick Diagnostic Commands

```bash
# Server health overview
echo "=== Disk ===" && df -h / && echo "=== Memory ===" && free -m && echo "=== CPU ===" && uptime && echo "=== Docker ===" && docker system df

# All Coolify containers
docker ps --filter "label=coolify.managed=true" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Recently stopped containers (crash history)
docker ps -a --filter "label=coolify.managed=true" --filter "status=exited" --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}"

# Container resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check for OOM events in the last hour
dmesg --time-format iso | grep -i oom | tail -5

# Traefik routing summary
docker exec coolify-proxy wget -qO- http://localhost:8080/api/http/routers 2>/dev/null | python3 -c "import json,sys;[print(r['rule'],r.get('status','')) for r in json.load(sys.stdin)]" 2>/dev/null || echo "Traefik API not accessible"
```
