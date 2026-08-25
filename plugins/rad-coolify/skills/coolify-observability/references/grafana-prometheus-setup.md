# Grafana + Prometheus Setup for Coolify

## Live-change gate

Before deploying monitoring resources or changing scrape targets, confirm the exact instance and resource, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

## Architecture

```
Container Metrics → cAdvisor → Prometheus → Grafana
                                   ↑
Server Metrics → Node Exporter ────┘
```

## Option 1: Deploy as Docker Compose Service in Coolify

Create a Docker Compose application in Coolify with this stack:

```yaml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - prometheus-data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:10.2.0
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_SERVER_ROOT_URL=https://grafana.example.com
    ports:
      - "3000"
    depends_on:
      - prometheus

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080"
    privileged: true
    devices:
      - /dev/kmsg

  node-exporter:
    image: prom/node-exporter:v1.7.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100"

volumes:
  prometheus-data:
  grafana-data:
```

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

## Option 2: Deploy on a Separate Monitoring Server

For production, run the monitoring stack on a different server to avoid competing for resources:

1. Deploy Prometheus + Grafana + Node Exporter on the monitoring server
2. Deploy only cAdvisor + Node Exporter on each Coolify application server
3. Configure Prometheus to scrape remote targets:

```yaml
scrape_configs:
  - job_name: 'coolify-server-1-cadvisor'
    static_configs:
      - targets: ['<COOLIFY_SERVER_IP>:8081']
        labels:
          server: 'coolify-1'

  - job_name: 'coolify-server-1-node'
    static_configs:
      - targets: ['<COOLIFY_SERVER_IP>:9100']
        labels:
          server: 'coolify-1'
```

**Security**: Restrict access to metric endpoints via firewall rules — only allow the monitoring server IP.

## Grafana Configuration

### Add Prometheus Data Source

1. Grafana → Settings → Data Sources → Add Data Source
2. Type: Prometheus
3. URL: `http://prometheus:9090` (if same compose stack) or `http://<PROMETHEUS_IP>:9090`
4. Save & Test

### Recommended Dashboards

Import these dashboards from grafana.com:

| Dashboard ID | Name | Shows |
|-------------|------|-------|
| 893 | Docker and System Monitoring | Container CPU, memory, network, disk |
| 1860 | Node Exporter Full | Server-level metrics |
| 14282 | cAdvisor - Docker Container Metrics | Per-container detailed metrics |
| 11600 | Docker Container & Host Metrics | Combined host and container view |

Import: Grafana → Dashboards → Import → Enter ID → Select Prometheus data source.

### Custom Dashboard: Coolify Overview

Create a dashboard with these panels:

**Row 1: Server Health**
- CPU Usage (gauge): `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Memory Usage (gauge): `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- Disk Usage (gauge): `(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100`

**Row 2: Container Resources**
- Container CPU by name: `rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100`
- Container Memory by name: `container_memory_usage_bytes{name=~".+"}`
- Container Network I/O: `rate(container_network_receive_bytes_total{name=~".+"}[5m])`

**Row 3: Container Status**
- Running containers (stat): `count(container_last_seen{name=~".+"})`
- Container restarts: `increase(container_restart_count{name=~".+"}[1h])`

## Alerting

### Prometheus Alert Rules

Create `alert.rules.yml`:

```yaml
groups:
  - name: coolify-alerts
    rules:
      - alert: HighCPUUsage
        expr: (1 - avg(irate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"

      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low on {{ $labels.instance }}"

      - alert: ContainerDown
        expr: absent(container_last_seen{name=~"app-.+"})
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} is down"

      - alert: ContainerHighMemory
        expr: container_memory_usage_bytes{name=~".+"} / container_spec_memory_limit_bytes{name=~".+"} > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} using >90% memory"

      - alert: HighContainerRestarts
        expr: increase(container_restart_count{name=~".+"}[1h]) > 3
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} restarted >3 times in 1 hour"
```

### Grafana Alert Integration

Use Grafana's built-in alerting to send alerts to:
- Slack
- Discord
- PagerDuty
- Email
- Webhook

Configure in: Grafana → Alerting → Contact Points → Add.

## Resource Estimates

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| Prometheus (30d retention, 10 containers) | 0.5 core | 512MB-1GB | 5-20GB |
| Grafana | 0.25 core | 256MB | 1GB |
| cAdvisor | 0.25 core | 128MB | Negligible |
| Node Exporter | 0.1 core | 64MB | Negligible |
| **Total** | **~1 core** | **~1.5GB** | **~25GB** |

For a server with 4GB RAM running production apps, consider running the monitoring stack on a separate server.
