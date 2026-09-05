# coolify-infrastructure operations

Read the matching section only. The entrypoint's scope and approval rules still apply. Paths in these examples are relative to the skill directory unless stated otherwise.

## Multi-Server Architecture

### How Coolify Multi-Server Works

Coolify runs on one **main server** and can manage additional **remote servers** via SSH:

```
┌──────────────────────┐     SSH     ┌──────────────────┐
│ Main Coolify Server  │────────────►│ Remote Server 1  │
│ (Dashboard + DB +    │             │ (Apps + DBs)     │
│  Proxy + Apps)       │             └──────────────────┘
│                      │     SSH     ┌──────────────────┐
│                      │────────────►│ Remote Server 2  │
│                      │             │ (Apps + DBs)     │
└──────────────────────┘             └──────────────────┘
```

### Adding a Remote Server

1. **Prepare the remote server**: Install Docker and ensure SSH is configured
2. **In Coolify UI**: Settings → Servers → Add Server
3. **Configure SSH**: Provide IP, port, SSH user, and SSH private key
4. **Validate**: Coolify tests the SSH connection and Docker availability
5. **Install Sentinel**: Coolify deploys its monitoring agent to the remote server

**Requirements for remote servers**:
- Docker installed and running
- SSH access from the main Coolify server (key-based auth)
- Ports open: SSH (22), HTTP (80), HTTPS (443) for Traefik on that server
- Coolify installs its own Traefik proxy on each remote server

### Deploying the Same App to Multiple Servers

This requires a **Docker Registry** because:
1. The image is built once (on the build server or main server)
2. The built image is pushed to a registry (GHCR, Docker Hub, private)
3. Each target server pulls the image from the registry
4. Without a registry, the image only exists on the build server

**Workflow**:
1. Configure a Docker Registry in Coolify (Settings → Docker Registries)
2. Create the application on the main server
3. In Application Settings → set the target server(s)
4. On deploy: Coolify builds → pushes to registry → each server pulls and runs

### Load Balancing Across Servers

Coolify does NOT provide built-in cross-server load balancing. Each server runs its own Traefik instance. To load balance:

**Option 1: External load balancer** (recommended):
- Use Cloudflare, AWS ALB, HAProxy, or Nginx as an external LB
- Point the LB to all server IPs running the app
- DNS round-robin is the simplest but least reliable

**Option 2: DNS load balancing**:
- Add multiple A records for the same domain pointing to different servers
- Simple but no health checking — a dead server still receives traffic

**Option 3: Cloudflare Load Balancing**:
- Cloudflare's paid LB feature with health checks
- Best option for most Coolify multi-server setups

## Docker Swarm (Experimental)

> **Warning**: Docker Swarm support in Coolify is **experimental**. Not all features work reliably. Use for testing and non-critical workloads only.

### Current Status

- Swarm mode can be initialized from the Coolify UI
- Basic service deployment works
- Some Coolify features may not work correctly in Swarm mode
- Community reports mixed results — stability varies by Coolify version

### Swarm Setup

1. **Minimum servers**: 1 manager + 1 worker (3 managers recommended for HA)
2. **Architecture**: All servers must be the same architecture (amd64 or arm64)
3. **Network**: All servers must be able to reach each other on ports:
   - 2377/tcp (cluster management)
   - 7946/tcp+udp (node communication)
   - 4789/udp (overlay network)

### Initialization

1. In Coolify: Server → Swarm → Initialize as Manager
2. Coolify runs `docker swarm init` on the main server
3. Add worker nodes: Server → Swarm → Join as Worker
4. Coolify runs `docker swarm join --token <TOKEN>` on worker servers

### Known Limitations in Swarm Mode

| Feature | Status |
|---------|--------|
| Application deployment | Works (basic) |
| Rolling updates | Works (uses Swarm's built-in rolling update) |
| Health checks | Works (Swarm-native) |
| Persistent volumes | Limited (volumes are node-local, not shared) |
| Docker Compose deploy | Partial (converted to Swarm stack) |
| PR preview environments | Not supported |
| Terminal access | Limited |
| Build on deploy | May require registry for multi-node builds |
| Database services | Works on single node; no replication |

### When to Use Swarm vs Multi-Server Without Swarm

| Criteria | Multi-Server (no Swarm) | Docker Swarm |
|----------|------------------------|--------------|
| **Complexity** | Lower | Higher |
| **Load balancing** | External LB needed | Swarm built-in routing mesh |
| **Service discovery** | Container names (same server) | Swarm service names (cross-server) |
| **Rolling updates** | Coolify-managed | Swarm-native |
| **Persistent storage** | Volumes per server | Node-local only (need NFS/Ceph for shared) |
| **Stability in Coolify** | More stable | Experimental |
| **Recommendation** | Production workloads | Testing/non-critical |

## Build Server Configuration

### Separate Build and Deployment Servers

For large or resource-intensive builds, offload the build process to a dedicated server:

1. **Add a server** in Coolify designated as the build server
2. **Configure the application**: In Application Settings → Build Server, select the dedicated build server
3. **Registry required**: The build server pushes the built image to a registry; the deployment server pulls it

**Benefits**:
- Build process doesn't consume deployment server resources
- Faster builds on a server with more CPU/RAM
- Production server stays responsive during builds

### Build Server Requirements

| Resource | Recommendation |
|----------|---------------|
| CPU | 4+ cores (builds are CPU-intensive) |
| RAM | 8GB+ (Node.js builds can be memory-hungry) |
| Disk | 50GB+ SSD (Docker build cache is large) |
| Network | Fast connection to Docker Registry |

## Coolify Instance Management

### Backup Strategy

Coolify stores its configuration and state in:
- `/data/coolify/` — main data directory
  - `source/` — Coolify source code and Docker Compose
  - `databases/` — Coolify's internal PostgreSQL database
  - `proxy/` — Traefik configuration and ACME certificates
  - `ssh/` — SSH keys for server management
  - `applications/` — Application data

**Automated backup**:

```bash
#!/bin/bash
# coolify-backup.sh — Run daily via cron

BACKUP_DIR="/backups/coolify"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/coolify_${TIMESTAMP}.tar.gz"

# Stop Coolify briefly for consistent backup
# NOTE: Running app containers are NOT affected — they continue serving via Traefik
# Only the Coolify dashboard becomes unavailable during this window (~1-2 minutes)
cd /data/coolify/source
docker compose stop

# Create backup
tar -czf "$BACKUP_FILE" /data/coolify/

# Restart Coolify
docker compose up -d

# Upload to S3 (optional)
aws s3 cp "$BACKUP_FILE" s3://<BUCKET>/coolify-backups/

# Retain last 30 backups locally
ls -t ${BACKUP_DIR}/coolify_*.tar.gz | tail -n +31 | xargs rm -f

echo "Backup completed: $BACKUP_FILE"
```

**Cron schedule**:
```bash
# Daily at 3 AM
0 3 * * * /opt/scripts/coolify-backup.sh >> /var/log/coolify-backup.log 2>&1
```

**What to back up**:
- `/data/coolify/` — everything
- Environment: document server OS, Docker version, Coolify version

**What NOT to back up** (too large, recreatable):
- Docker images (pulled from registry on deploy)
- Build cache (rebuilt on next deploy)

### Migration to New Server

1. **On old server**: Stop Coolify and create a backup
   ```bash
   cd /data/coolify/source
   docker compose stop
   tar -czf /tmp/coolify-migration.tar.gz /data/coolify/
   ```

2. **On new server**: Install the selected Coolify release
   - Choose a tagged release from the official Coolify release notes.
   - Download the matching installer to a file from its versioned release URL. Do not pipe a mutable URL to a shell.
   - Verify the published checksum or signature, inspect the script, then run it with the exact version and target recorded.

3. **Stop fresh Coolify and restore data**:
   ```bash
   cd /data/coolify/source
   docker compose stop
   cd /
   sudo mv /data/coolify /data/coolify-pre-restore-<TIMESTAMP>
   sudo mkdir /data/coolify
   tar -xzf /tmp/coolify-migration.tar.gz -C /
   ```
   Keep the pre-restore directory until the restored instance is verified. This makes the change recoverable and avoids a recursive delete.

4. **Start Coolify**:
   ```bash
   cd /data/coolify/source
   docker compose up -d
   ```

5. **Update DNS**: Point your Coolify dashboard domain to the new server IP

6. **Update remote servers**: If remote servers had the old server's SSH key, re-validate connections

7. **Verify**: Check all applications are running, SSL certificates are valid

### Coolify Self-Update

```bash
# Recommended: Via UI
# Settings → Update → Check for updates → Install

# Via a checked installer file
# 1. Select the exact release from the official Coolify release notes.
# 2. Download its versioned installer, verify its checksum or signature, and inspect it.
# 3. Run the local file only after stating the exact server and version.
sudo bash /tmp/coolify-install-<VERSION>.sh
```

**Before updating**:
- Create a backup of `/data/coolify/`
- Get user acceptance for the exact server, release, and update action
- Read the release notes for breaking changes
- Test in staging if running critical production workloads
