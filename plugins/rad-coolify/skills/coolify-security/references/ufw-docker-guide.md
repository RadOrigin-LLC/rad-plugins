# UFW + Docker Integration Guide

## Live-change gate

Before changing UFW or Docker firewall rules, confirm the exact instance and server, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

## The Core Problem

Docker manipulates `iptables` directly, inserting rules in the `DOCKER-USER` and `DOCKER` chains that take precedence over UFW's rules. This means:

```
UFW rule: deny 5432           → Ignored by Docker
Docker:   -p 5432:5432        → Port is publicly accessible

Result: Your database is exposed to the internet
        even though UFW says it's blocked.
```

This is one of the most common and dangerous misconfigurations in Docker-based deployments.

## Solution: ufw-docker

The `ufw-docker` utility creates iptables rules in the correct chain so that UFW rules apply to Docker containers.

### Installation

```bash
# Download a selected tagged release to a file, then verify its published
# SHA-256 checksum before installing it. Do not pipe a remote URL to a shell.
VERSION="<VERIFIED_RELEASE_TAG>"
EXPECTED_SHA256="<SHA256_FROM_OFFICIAL_RELEASE>"
curl --fail --location --output "/tmp/ufw-docker-${VERSION}" \
  "https://github.com/chaifeng/ufw-docker/releases/download/${VERSION}/ufw-docker"
ACTUAL_SHA256=$(sha256sum "/tmp/ufw-docker-${VERSION}" | cut -d' ' -f1)
test "$ACTUAL_SHA256" = "$EXPECTED_SHA256"
sudo install -m 0755 "/tmp/ufw-docker-${VERSION}" /usr/local/bin/ufw-docker

# Install the iptables rules
sudo ufw-docker install

# Verify installation
sudo ufw-docker status
```

### Basic Usage

```bash
# Allow external access to a container's port
sudo ufw-docker allow <CONTAINER_NAME> <PORT>/tcp

# Allow from specific IP only
sudo ufw-docker allow <CONTAINER_NAME> <PORT>/tcp from <IP_ADDRESS>

# Deny access (remove a previous allow)
sudo ufw-docker delete allow <CONTAINER_NAME> <PORT>/tcp

# List current rules
sudo ufw-docker status

# Remove all ufw-docker rules for a container
sudo ufw-docker delete allow <CONTAINER_NAME>
```

### Common Scenarios

#### Expose Database to Specific IP

```bash
# Allow your office IP to access PostgreSQL
sudo ufw-docker allow postgres-container 5432/tcp from 203.0.113.50

# Allow your home IP too
sudo ufw-docker allow postgres-container 5432/tcp from 198.51.100.25
```

#### Expose Application Port

```bash
# Usually not needed — Traefik handles HTTP/HTTPS routing
# Only needed for non-HTTP services
sudo ufw-docker allow my-game-server 7777/udp
```

#### Block Everything Except Traefik

```bash
# This is the default behavior after installing ufw-docker:
# - Traefik on ports 80/443 is allowed via UFW
# - All other container ports are blocked unless explicitly allowed
# - Internal container-to-container traffic is unaffected
```

## Alternative: Disable Docker iptables (Not Recommended)

```json
// /etc/docker/daemon.json
{
  "iptables": false
}
```

**Why not recommended**:
- Breaks inter-container networking
- Breaks Docker DNS resolution between containers
- Requires manual iptables rules for everything
- Easy to misconfigure, leaving containers unreachable

Only use this if you have deep iptables expertise and specific requirements.

## Alternative: Bind to localhost only

For ports that should only be accessible from the server itself:

```yaml
# In docker-compose.yml or Coolify port mapping
ports:
  - "127.0.0.1:5432:5432"   # Only accessible from the host
  # NOT: "5432:5432"         # This binds to 0.0.0.0 (all interfaces)
```

This is the simplest and most reliable approach for databases that only need local access (app containers can still reach them via the Docker network).

## Verification

After setting up ufw-docker:

```bash
# Check that ports are NOT accessible externally
# From a different machine:
nmap -p 5432 <SERVER_IP>
# Should show: filtered or closed

# Check that container-to-container networking works
# From inside an app container:
docker exec <APP_CONTAINER> curl http://<DB_CONTAINER>:5432
# Should connect (or get a protocol error — but NOT a timeout)

# Check iptables rules
sudo iptables -L DOCKER-USER -n -v
# Should show ufw-docker rules
```

## Coolify-Specific Considerations

### Ports Coolify Needs Open

| Port | Service | Required |
|------|---------|----------|
| 22 | SSH | Yes (Coolify uses SSH to manage remote servers) |
| 80 | HTTP (Traefik) | Yes |
| 443 | HTTPS (Traefik) | Yes |
| 8000 | Coolify Dashboard | Yes (only from admin IPs) |
| 6001 | Coolify Realtime (websocket) | Yes (for dashboard) |
| 6002 | Coolify Sentinel | Internal only (managed by Coolify) |

### Securing the Coolify Dashboard

```bash
# Allow dashboard access only from trusted IPs
sudo ufw allow from 203.0.113.50 to any port 8000
sudo ufw allow from 203.0.113.50 to any port 6001

# Or use a VPN/tunnel and only allow localhost
sudo ufw allow from 127.0.0.1 to any port 8000
```

### Multi-Server Ports

If using multiple Coolify servers:

```bash
# Allow SSH between Coolify servers
sudo ufw allow from <COOLIFY_MAIN_IP> to any port 22

# Allow Docker Swarm ports (if using Swarm)
sudo ufw allow from <SWARM_PEER_IP> to any port 2377/tcp  # Swarm manager
sudo ufw allow from <SWARM_PEER_IP> to any port 7946      # Node communication
sudo ufw allow from <SWARM_PEER_IP> to any port 4789/udp  # Overlay network
```
