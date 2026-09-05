# coolify-security operations

Read the matching section only. The entrypoint's scope and approval rules still apply. Paths in these examples are relative to the skill directory unless stated otherwise.

## Secrets Management

### Three Types of Secrets in Coolify

| Type | Scope | Visibility | Use For |
|------|-------|------------|---------|
| **Runtime Env Vars** | Running container | Visible via `docker inspect` | Database URLs, API keys, feature flags |
| **Build-time Env Vars** | Build process | Visible in build logs + image layers | npm tokens, build-time API keys |
| **Docker Build Secrets** | Build process only | NOT in image layers or logs | Private registry tokens, signing keys |

### Decision Tree: Where to Put a Secret

```
START: When is this secret needed?
│
├─ Only at runtime (app needs it while running)?
│  └─► Runtime Environment Variable
│      Set "Build Variable" = OFF in Coolify
│
├─ Only at build time (npm install, Docker build)?
│  ├─ Is it acceptable if this value appears in image layers?
│  │  ├─ Yes → Build-time Environment Variable
│  │  └─ No  → Docker Build Secret
│  │          (requires Dockerfile with --mount=type=secret)
│  │
│  └─ None of the above → Docker Build Secret (safest)
│
├─ Needed at both build AND runtime?
│  └─► Two separate entries: one build-time, one runtime
│      Do NOT use build-time alone (baked into image)
│
└─ Shared across multiple apps?
   └─► Shared Environment Variable (project-level or team-level)
       Coolify supports shared variables that multiple resources reference
```

### Docker Build Secrets Pattern

For secrets that must not appear in image layers:

**In Coolify**: Enable "Use Docker Build Secrets" checkbox on the environment variable. Coolify automatically:
1. Passes each build variable via `--secret id=KEY,env=KEY` instead of `--build-arg`
2. Prepends `# syntax=docker/dockerfile:1` to the Dockerfile if missing
3. Auto-injects `--mount=type=secret` into every `RUN` instruction (no manual Dockerfile changes needed)
4. Generates `COOLIFY_BUILD_SECRETS_HASH` to maintain build cache integrity

**No Dockerfile modification required** — Coolify handles the BuildKit secret injection automatically. Coolify uses BuildKit by default, so this works without additional server configuration.

**Manual Dockerfile approach** (if you prefer explicit control):
```dockerfile
# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
COPY . .
RUN npm run build
```

### Shared Variables

Shared-variable scopes and interpolation syntax can change between Coolify releases. Check the instance at use time:

1. Run `coolify context verify` and read the exact instance version.
2. Inspect the current project, environment, team, and server settings for the scopes exposed there.
3. Use only the interpolation syntax shown by that instance, and redeploy the affected resources after a change.

Do not copy a scope or syntax from an older guide into a production environment without this check.

## RBAC (Role-Based Access Control)

### Team Roles

| Role | Capabilities | Limitations |
|------|-------------|-------------|
| **Owner** | Full access: create/delete all resources, manage team members, access all settings, view/edit all secrets, terminal access, manage servers and billing | None |
| **Admin** | Manage apps/databases/projects, delete member-created resources, modify terminal access settings | Cannot delete owner-created resources, cannot manage users or servers |
| **Member** | View and collaborate on assigned projects, see redacted secrets, delete own deployments | Cannot manage team members, cannot modify server settings, limited secret visibility |

### Permission Scope

Coolify v4 RBAC operates at the **team** level:
- Each team has its own servers, projects, and resources
- Users can belong to multiple teams with different roles
- Resources (servers, apps, databases) belong to a team
- No per-app or per-server granular permissions within a team
- API tokens are team-scoped. Current permissions are `read`, `read:sensitive`, `deploy`, `write`, and `root`.
- Use `read` for status. Add `read:sensitive` for logs or sensitive fields, `deploy` for deployments and lifecycle controls, and `write` for application or environment changes.
- `root` gives complete API control and is unnecessary for normal deployment work.
- Coolify Private Keys are SSH keys for server access or private Git deploy keys. Never supply one as `COOLIFY_API_TOKEN`.

### Known RBAC Limitations

- No per-resource permissions (e.g., "admin can deploy app A but not app B") — planned for v4 stable or v5
- No custom roles (only Owner/Admin/Member)
- No SAML/LDAP/OIDC natively — only OAuth via GitHub, GitLab, Google, Azure, Bitbucket
- Confirm the current instance audit and activity features before relying on them for change tracking.
- Terminal access is all-or-nothing per server (cannot selectively disable for Members while keeping it for Admins)
- Review environment-variable scope for every Compose service on the exact instance before deployment.

**Workaround for per-app isolation**: Create separate teams for each project or security boundary. Each team has its own resources and RBAC.

## Network Isolation

### The `coolify` Docker Network

All Coolify-managed containers join the `coolify` Docker network (bridge mode):

- **All containers on the same server CAN reach each other** by container name
- Traefik routes external HTTP/HTTPS traffic to containers
- Non-HTTP ports are not exposed externally by default

### Isolating Apps from Each Other

To prevent two apps on the same server from communicating:

1. **Separate Docker networks** — Coolify does not natively support per-app networks. Workaround: use Docker Compose with custom networks.
2. **Separate servers** — The only guaranteed isolation is running on different servers.
3. **Application-level firewall** — Use iptables rules inside the container (complex, fragile).

**Reality**: Coolify's networking model assumes trust within a server. For true multi-tenant isolation, use separate servers or a container orchestrator with network policies (Kubernetes).

### Exposing Ports

| Method | Access | Use For |
|--------|--------|---------|
| **Traefik routing (default)** | HTTP/HTTPS only, via domain | Web applications |
| **Port mapping** | Any TCP/UDP port on host | Databases, custom protocols |
| **No exposure** | Internal only (coolify network) | Background workers, internal services |

**Security rule**: Only expose ports that must be accessible externally. Default to internal-only.

## UFW and Docker — The Known Conflict

### The Problem

Docker modifies `iptables` directly, bypassing UFW rules. This means:
- UFW `deny` rules do NOT block Docker-published ports
- A database exposed on port 5432 is accessible to the internet even if UFW blocks 5432

### The Fix

```bash
# Option 1: Disable Docker's iptables manipulation (affects ALL containers)
# /etc/docker/daemon.json
{
  "iptables": false
}
# Then restart Docker: systemctl restart docker
# WARNING: This breaks inter-container networking; requires manual iptables rules

# Option 2 (Recommended): Use ufw-docker utility after a checked install.
# 1. Select a tagged release in the official ufw-docker repository.
# 2. Download its release asset to a temporary file. Do not pipe a remote URL to a shell.
# 3. Verify the published SHA-256 checksum, inspect the file, then install it:
VERSION="<VERIFIED_RELEASE_TAG>"
EXPECTED_SHA256="<SHA256_FROM_OFFICIAL_RELEASE>"
curl --fail --location --output "/tmp/ufw-docker-${VERSION}" \
  "https://github.com/chaifeng/ufw-docker/releases/download/${VERSION}/ufw-docker"
ACTUAL_SHA256=$(sha256sum "/tmp/ufw-docker-${VERSION}" | cut -d' ' -f1)
test "$ACTUAL_SHA256" = "$EXPECTED_SHA256"
sudo install -m 0755 "/tmp/ufw-docker-${VERSION}" /usr/local/bin/ufw-docker
sudo ufw-docker install

# Allow specific access
ufw-docker allow <CONTAINER_NAME> 5432/tcp
ufw-docker allow <CONTAINER_NAME> 5432/tcp from 203.0.113.50
```

### Best Practice

- Bind database ports to `127.0.0.1` only: `127.0.0.1:5432:5432` (not `0.0.0.0:5432:5432`)
- Use SSH tunnels for remote database access instead of exposing ports
- Install a checked, versioned `ufw-docker` release to make UFW rules apply to Docker containers

## Resource Limits

### Setting Limits

In application or database settings:

| Setting | Purpose | Default |
|---------|---------|---------|
| **Memory Limit** | Maximum memory the container can use | Unlimited (dangerous) |
| **Memory Reservation** | Soft limit / guaranteed minimum | Not set |
| **CPU Limit** | Maximum CPU cores (e.g., `1.5`) | Unlimited |
| **CPU Reservation** | Guaranteed CPU minimum | Not set |

### OOM Behavior

When a container hits its memory limit:
1. Docker's OOM killer terminates the container process
2. Coolify's restart policy (`unless-stopped`) restarts the container
3. If the container OOMs repeatedly, it enters a restart loop
4. Check with: `docker inspect <CONTAINER> | grep -i oom`

### Build Process Limits

Build processes do NOT have separate resource limits in Coolify. A runaway build can consume all server resources. Mitigation:
- Use a separate build server (see coolify-infrastructure)
- Set `NODE_OPTIONS=--max-old-space-size=2048` for Node.js builds
- Monitor server resources during builds

## Terminal Access and Auditing

### Terminal Access

Coolify provides a **web terminal** in the UI for running commands inside containers:
- Admin and Developer roles can access the terminal
- Viewer role cannot access the terminal
- Terminal sessions are not logged or audited

### Locking Down Terminal Access

- Assign the **Viewer** role to team members who should not have shell access
- Create separate teams with appropriate roles for different access levels
- There is no way to allow deployment but deny terminal access within the same role

### Audit Logging

**Current state**: Coolify v4 has limited audit logging:
- Deployment history is logged (who triggered, when, status)
- Environment variable changes are NOT audited
- Terminal sessions are NOT logged
- API access is NOT logged per-request

**Workaround**: Enable server-level auditd for SSH and Docker command logging.
