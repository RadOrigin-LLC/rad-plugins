# Multi-Server Setup Guide

## Live-change gate

Before adding a server, changing firewall rules, or deploying a remote resource, confirm the exact instance and server, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

## Prerequisites

### Main Coolify Server
- Coolify v4.x installed and running
- Docker Registry configured (GHCR, Docker Hub, or self-hosted)
- SSH key pair for connecting to remote servers

### Remote Servers
- Ubuntu 22.04+ or Debian 12+ (recommended)
- Docker installed from the operating system's checked package instructions. Download a versioned package or installer, verify its checksum or signature, inspect it, then install it. Do not pipe a mutable remote script to a shell.
- SSH server running with key-based authentication
- Firewall configured to allow SSH from the main Coolify server

## Step-by-Step Setup

### 1. Prepare SSH Key

On the main Coolify server:

```bash
# Generate a dedicated key (if not already done)
ssh-keygen -t ed25519 -f /root/.ssh/coolify_remote -N ""

# Copy public key to remote server
ssh-copy-id -i /root/.ssh/coolify_remote.pub root@<REMOTE_IP>

# Test connection
ssh -i /root/.ssh/coolify_remote root@<REMOTE_IP> "docker info --format '{{.ServerVersion}}'"
```

### 2. Add Remote Server in Coolify

1. Navigate to **Servers → Add Server**
2. Fill in:
   - **Name**: Descriptive name (e.g., "production-app-server-2")
   - **IP Address**: Remote server IP
   - **SSH Port**: 22 (or custom)
   - **SSH User**: root (or user with Docker access)
   - **SSH Private Key**: Paste the private key content
3. Click **Validate** — Coolify tests SSH connection and Docker availability
4. **Save** — Coolify installs Sentinel and Traefik on the remote server

### 3. Configure Docker Registry

Before deploying to remote servers, set up a registry:

**GHCR (recommended)**:
1. Settings → Docker Registries → Add
2. URL: `ghcr.io`
3. Username: GitHub username
4. Password: GitHub PAT with `read:packages` and `write:packages`

**Self-hosted Registry** (for air-gapped or private environments):
```bash
# On any server accessible to all Coolify servers
docker run -d -p 5000:5000 --restart always --name registry registry:2

# In Coolify: Settings → Docker Registries → Add
# URL: <REGISTRY_SERVER_IP>:5000
# No username/password for a basic setup
```

### 4. Deploy Application to Remote Server

1. Create a new application (or edit existing)
2. In **Application Settings → Server**, select the remote server
3. Configure the Docker Registry to use for this application
4. Deploy — Coolify:
   - Builds the image on the build server (or main server)
   - Pushes to the registry
   - SSHs into the remote server
   - Pulls the image from the registry
   - Starts the container with Traefik labels

### 5. Configure DNS

Point your application domain to the remote server's IP (not the main Coolify server):
- The remote server runs its own Traefik instance
- SSL certificates are provisioned on the remote server

## Load Balancing Configuration

### Cloudflare Load Balancing

1. In Cloudflare dashboard → Traffic → Load Balancing
2. Create a pool with all server IPs running the app
3. Configure health checks:
   - Monitor: HTTP
   - Path: `/healthz`
   - Interval: 60s
4. Create a load balancer attached to your domain
5. Traffic is distributed with health checking

### Nginx Load Balancer (Self-Hosted)

Deploy on a separate server:

```nginx
upstream coolify_app {
    least_conn;
    server <SERVER_1_IP>:443;
    server <SERVER_2_IP>:443;
}

server {
    listen 443 ssl;
    server_name app.example.com;

    ssl_certificate /etc/ssl/app.example.com.pem;
    ssl_certificate_key /etc/ssl/app.example.com.key;

    location / {
        proxy_pass https://coolify_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /healthz {
        proxy_pass https://coolify_app;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }
}
```

### HAProxy Load Balancer

```haproxy
frontend https
    bind *:443 ssl crt /etc/ssl/app.pem
    default_backend coolify_servers

backend coolify_servers
    balance roundrobin
    option httpchk GET /healthz
    http-check expect status 200
    server server1 <SERVER_1_IP>:443 ssl verify none check inter 10s
    server server2 <SERVER_2_IP>:443 ssl verify none check inter 10s
```

## Shared State Across Servers

When running the same app on multiple servers, handle shared state:

### Session Storage
- **DO NOT** use local filesystem sessions
- Use Redis or a database for session storage
- Deploy a shared Redis instance accessible to all servers

### File Uploads
- **DO NOT** store uploads on the local filesystem
- Use S3-compatible storage (AWS S3, MinIO, DigitalOcean Spaces)
- Or mount a shared NFS volume across servers

### Database
- Use a central database server (separate from app servers)
- Or use a managed database service (RDS, Supabase, PlanetScale)
- All app servers connect to the same database

## Networking Between Servers

### Required Ports

| From | To | Port | Purpose |
|------|----|------|---------|
| Main Coolify | Remote Servers | 22/tcp | SSH management |
| Remote Servers | Docker Registry | 443/tcp | Image pull |
| Users | Remote Servers | 80/tcp, 443/tcp | HTTP/HTTPS traffic |
| Main Coolify | Remote Servers | 6002/tcp | Sentinel communication |

### Firewall Rules (Remote Server)

```bash
# Allow SSH from Coolify main server
ufw allow from <MAIN_COOLIFY_IP> to any port 22

# Allow HTTP/HTTPS from the internet (or load balancer only)
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Sentinel from Coolify main server
ufw allow from <MAIN_COOLIFY_IP> to any port 6002

# Deny everything else
ufw default deny incoming
ufw enable
```

## Troubleshooting Multi-Server

| Issue | Cause | Fix |
|-------|-------|-----|
| Deploy fails with "image not found" on remote | Registry not configured or credentials wrong | Check Docker Registry settings in Coolify |
| SSH connection refused | Firewall blocking, SSH not running, wrong key | Test SSH manually: `ssh -i <KEY> <USER>@<IP>` |
| Traefik not starting on remote | Port conflict or Docker network issue | SSH in, check: `docker logs coolify-proxy` |
| Sentinel not reporting | Port 6002 blocked or Sentinel not installed | Check firewall; reinstall Sentinel from Coolify UI |
| SSL cert not provisioning on remote | DNS not pointing to remote server IP | Verify: `dig <DOMAIN>` shows remote server IP |
| Slow image pulls | Remote server far from registry | Use a registry closer to remote servers or a caching proxy |
