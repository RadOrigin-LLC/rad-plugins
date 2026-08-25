# Docker Swarm Guide for Coolify

## Live-change gate

Before initializing or changing Swarm, confirm the exact Coolify instance and server, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

> **Experimental in Coolify.** This guide documents behavior that may change between releases. Check the exact instance version and current Coolify documentation before using Swarm.

> **Docker Swarm itself is supported through 2030** by Mirantis (the orchestration vendor). It is not deprecated by Docker. The "experimental" label is about Coolify's integration completeness, not Swarm's viability.

> **Operational caution:** In Swarm environments, inspect old container cleanup after rolling updates. Monitor `docker service ps <service-name>` and use the current Coolify and Docker documentation before removing stale replicas.

## Swarm Overview in Coolify

Docker Swarm provides native container orchestration with:
- Built-in load balancing via routing mesh
- Service discovery across nodes
- Rolling updates
- Self-healing (restart failed containers on healthy nodes)

Coolify integrates with Swarm to manage deployments through its UI/API, but not all Coolify features are compatible.

## Prerequisites

### Server Requirements

| Role | Minimum Servers | Recommended |
|------|----------------|-------------|
| Manager | 1 | 3 (for HA quorum) |
| Worker | 0+ | 2+ (for workload distribution) |

**All servers must**:
- Run the same Docker version
- Be the same CPU architecture (all amd64 OR all arm64, not mixed)
- Have network connectivity on required ports
- Have Coolify Sentinel installed (done automatically)

### Network Requirements

| Port | Protocol | Purpose |
|------|----------|---------|
| 2377 | TCP | Cluster management (manager ↔ manager) |
| 7946 | TCP + UDP | Node discovery and communication |
| 4789 | UDP | Overlay network (VXLAN) |

**Firewall rules** (on all Swarm nodes):
```bash
# Allow Swarm traffic between all Swarm members
for PEER_IP in <MANAGER_IPS> <WORKER_IPS>; do
  ufw allow from $PEER_IP to any port 2377 proto tcp
  ufw allow from $PEER_IP to any port 7946
  ufw allow from $PEER_IP to any port 4789 proto udp
done
```

## Initialization

### Step 1: Initialize Swarm Manager

In Coolify UI:
1. Navigate to the main server → **Swarm** tab
2. Click **Initialize as Swarm Manager**
3. Coolify runs `docker swarm init --advertise-addr <SERVER_IP>`

Or manually via SSH:
```bash
docker swarm init --advertise-addr <MAIN_SERVER_IP>
```

### Step 2: Get Join Tokens

```bash
# Worker join token
docker swarm join-token worker

# Manager join token (for additional managers)
docker swarm join-token manager
```

### Step 3: Join Worker Nodes

In Coolify UI:
1. Navigate to the remote server → **Swarm** tab
2. Click **Join as Worker**
3. Coolify runs the join command on the remote server

Or manually:
```bash
docker swarm join --token <WORKER_TOKEN> <MANAGER_IP>:2377
```

### Step 4: Verify Swarm Status

```bash
# On any manager node
docker node ls

# Expected output:
# ID              HOSTNAME       STATUS  AVAILABILITY  MANAGER STATUS
# abc123...  *    manager-1      Ready   Active        Leader
# def456...       worker-1       Ready   Active
# ghi789...       worker-2       Ready   Active
```

## Deploying Applications in Swarm Mode

When Swarm mode is active:
1. Applications are deployed as Docker services (not standalone containers)
2. Swarm distributes replicas across available nodes
3. The routing mesh handles load balancing
4. Rolling updates are Swarm-native

### Replica Configuration

Set the number of replicas in the application settings:
- 1 replica = single instance (no HA)
- 2+ replicas = distributed across nodes with load balancing

### Rolling Update Configuration

Swarm manages rolling updates with configurable parameters:
- **Update parallelism**: How many containers to update at once
- **Update delay**: Wait time between batches
- **Failure action**: Pause, continue, or rollback on failure

## Feature Compatibility Matrix

| Coolify Feature | Swarm Status | Notes |
|----------------|-------------|-------|
| Application deployment | ✅ Works | Deployed as Swarm service |
| Rolling updates | ✅ Works | Swarm-native rolling update |
| Health checks | ✅ Works | Swarm health check integration |
| Environment variables | ✅ Works | Injected into service definition |
| Traefik routing | ⚠️ Partial | Requires overlay network configuration |
| Persistent volumes | ⚠️ Limited | Volumes are node-local, not shared |
| Docker Compose | ⚠️ Partial | Converted to Swarm stack; some features lost |
| PR preview deployments | ❌ Not supported | |
| Terminal access | ⚠️ Limited | Only to containers on the current node |
| Database services | ⚠️ Limited | Single-node only; no built-in replication |
| Build on deploy | ⚠️ Requires registry | Image must be in registry for multi-node |
| Log viewing | ⚠️ Partial | `docker service logs` works; UI may not aggregate |
| Rollback via UI | ⚠️ Partial | Swarm has its own rollback mechanism |

## Persistent Storage in Swarm

The biggest challenge with Swarm is storage:

### Problem
Docker volumes are node-local. If a container moves to a different node, its volume doesn't follow.

### Solutions

**NFS volumes** (simplest):
```bash
# On a file server
sudo apt install nfs-kernel-server
echo "/shared/data *(rw,sync,no_subtree_check)" >> /etc/exports
sudo exportfs -ra

# On each Swarm node
sudo apt install nfs-common
docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=<NFS_SERVER>,rw \
  --opt device=:/shared/data \
  app-data
```

**Constraint placement** (simplest but no HA):
```yaml
deploy:
  placement:
    constraints:
      - node.hostname == worker-1
```
This pins the service to one node, ensuring the volume is always there.

**GlusterFS or Ceph** (production-grade):
More complex but provides truly distributed storage. Beyond the scope of this guide.

## Monitoring Swarm

```bash
# Swarm overview
docker node ls
docker service ls

# Service details
docker service ps <SERVICE_NAME>
docker service logs <SERVICE_NAME>

# Node resource usage
docker node inspect <NODE_ID> --format '{{json .Status}}'

# Drain a node for maintenance
docker node update --availability drain <NODE_ID>

# Return node to service
docker node update --availability active <NODE_ID>
```

## Swarm vs Kubernetes

If you're considering Swarm for production, evaluate whether Kubernetes (via k3s or similar) might be more appropriate:

| Criteria | Docker Swarm | Kubernetes (k3s) |
|----------|-------------|-------------------|
| Complexity | Low | Medium-High |
| Learning curve | Small | Large |
| Coolify support | Experimental | Not supported |
| Community/ecosystem | Declining | Very active |
| Storage solutions | Limited | Mature (CSI) |
| Networking | Basic overlay | Advanced (CNI) |
| Auto-scaling | No | Yes |
| Service mesh | No | Yes (Istio, Linkerd) |

**Recommendation for Coolify users**: If you need more than what Coolify's multi-server (no Swarm) offers, consider:
1. Coolify multi-server with external load balancer (simplest)
2. Docker Swarm (if you want built-in orchestration and accept the experimental status)
3. Move to Kubernetes (if you've outgrown Coolify's orchestration capabilities)

## Disabling Swarm

If Swarm isn't working well:

```bash
# On worker nodes first
docker swarm leave

# On the manager (force if last manager)
docker swarm leave --force
```

Applications will need to be redeployed as standalone containers after leaving Swarm.
