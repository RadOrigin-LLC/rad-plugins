# Coolify Security Hardening Checklist

## Live-change gate

Before changing host access or firewall rules, confirm the exact instance and server, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

## Server-Level Hardening

### 1. SSH Configuration

```bash
# /etc/ssh/sshd_config
PermitRootLogin no               # Disable root SSH login
PasswordAuthentication no         # Key-only authentication
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers deploy coolify         # Restrict to specific users
Port 22022                        # Change default port (optional but reduces noise)

# Apply changes
sudo systemctl restart sshd
```

### 2. Firewall (UFW) Base Rules

```bash
# Reset to clean state
sudo ufw reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (use custom port if changed)
sudo ufw allow 22/tcp          # or 22022/tcp if changed

# Allow HTTP/HTTPS for Traefik
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Coolify UI (if on non-standard port)
sudo ufw allow 8000/tcp        # Coolify dashboard default

# Enable
sudo ufw enable
```

### 3. Install ufw-docker (Critical)

Without this, Docker bypasses all UFW rules:

```bash
# Select a tagged release, download its asset to a file, verify its published
# SHA-256 checksum, inspect it, then install the exact file.
VERSION="<VERIFIED_RELEASE_TAG>"
EXPECTED_SHA256="<SHA256_FROM_OFFICIAL_RELEASE>"
curl --fail --location --output "/tmp/ufw-docker-${VERSION}" \
  "https://github.com/chaifeng/ufw-docker/releases/download/${VERSION}/ufw-docker"
ACTUAL_SHA256=$(sha256sum "/tmp/ufw-docker-${VERSION}" | cut -d' ' -f1)
test "$ACTUAL_SHA256" = "$EXPECTED_SHA256"
sudo install -m 0755 "/tmp/ufw-docker-${VERSION}" /usr/local/bin/ufw-docker

# Install the iptables rules
sudo ufw-docker install

# Restart UFW
sudo ufw reload
```

### 4. Automatic Security Updates

```bash
# Ubuntu/Debian
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Verify
cat /etc/apt/apt.conf.d/20auto-upgrades
```

### 5. Fail2Ban

```bash
sudo apt install fail2ban

# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 22           # Match your SSH port
maxretry = 5
bantime = 3600
findtime = 600
```

## Coolify-Level Hardening

### 6. API Token Management

- Generate separate API tokens for each CI/CD pipeline
- Use descriptive names for tokens (e.g., "github-actions-staging-2024")
- Rotate tokens quarterly or after team member departures
- Delete unused tokens immediately

### 7. Environment Variable Hygiene

**Audit all env vars**:
```bash
# List all env vars for an application (on server)
docker exec <CONTAINER> env | sort
```

**Rules**:
- No real values in build-time variables unless absolutely necessary
- Use Docker Build Secrets for npm tokens, private keys
- Never store credentials in Dockerfile or docker-compose.yml files
- Review that build logs don't leak secrets (check deployment logs in UI)

### 8. Team and Role Configuration

```
Principle of Least Privilege:
├─ Production team: Only Admins who need to manage infrastructure
├─ Developer team: Developers who deploy to staging
├─ Observer team: Viewers who monitor dashboards
└─ CI/CD: Separate API tokens per pipeline (no human accounts)
```

### 9. Container Security

**Dockerfile best practices**:
```dockerfile
# Run as non-root user
RUN addgroup -g 1001 app && adduser -u 1001 -G app -s /bin/sh -D app
USER app

# No install of unnecessary packages
# No curl/wget in production image (reduces attack surface)
# Use multi-stage builds to exclude build tools
```

**Never use in production**:
- `--privileged` flag
- `--cap-add=ALL`
- `--pid=host`
- `--network=host`

### 10. SSL/TLS Configuration

- Let Traefik handle SSL termination (default behavior)
- Use Let's Encrypt certificates (auto-renewed by Coolify)
- For custom domains, ensure DNS points correctly before enabling SSL
- Force HTTPS redirect (enabled by default in Coolify)
- Set `Strict-Transport-Security` header

### 11. Database Security

- Never use default passwords (Coolify generates random passwords — keep them)
- Do not expose database ports unless absolutely necessary
- Use SSH tunnels for remote database access
- Set memory limits on all database containers
- Enable SSL for cross-server database connections

### 12. Backup Security

- Encrypt backups at rest (S3 server-side encryption)
- Use IAM roles with minimal permissions for backup access
- Store backup credentials separately from application credentials
- Test restore procedures regularly

## Monitoring for Security

### 13. Log Review

```bash
# Check for unauthorized SSH attempts
sudo journalctl -u sshd --since "1 hour ago" | grep "Failed"

# Check Docker events
docker events --since "1h" --filter "type=container"

# Check Coolify proxy logs
docker logs coolify-proxy 2>&1 | grep -i "error\|denied\|unauthorized"
```

### 14. Container Runtime Monitoring

```bash
# Check for containers running as root
docker ps -q | xargs docker inspect --format '{{.Name}} User={{.Config.User}}' | grep "User=$"

# Check for privileged containers
docker ps -q | xargs docker inspect --format '{{.Name}} Privileged={{.HostConfig.Privileged}}' | grep "true"

# Check exposed ports
docker ps --format "{{.Names}} {{.Ports}}" | grep "0.0.0.0"
```

## Security Incident Response

### If a Container Is Compromised

1. **Isolate**: Stop the container immediately (`docker stop <CONTAINER>`)
2. **Preserve evidence**: `docker export <CONTAINER> > evidence.tar` before removing
3. **Rotate all credentials**: API tokens, database passwords, env vars
4. **Check lateral movement**: Review other containers on the same server
5. **Rebuild from clean image**: Never restart a compromised container
6. **Review access logs**: Check Coolify deployment history, SSH logs
7. **Post-mortem**: Document attack vector and close the gap

### If Coolify Itself Is Compromised

1. **Do NOT access the UI** (attacker may have modified it)
2. SSH into the server directly
3. Check Coolify container integrity: `docker logs coolify`
4. Rotate the root admin password
5. Regenerate all API tokens
6. Review all application environment variables for tampering
7. Consider reinstalling Coolify from scratch
