# coolify-observability operations

Read the matching section only. The entrypoint's scope and approval rules still apply. Paths in these examples are relative to the skill directory unless stated otherwise.

## Observability Architecture

```
┌─────────────────────────────────────────────────────┐
│ Coolify Server                                       │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │ Sentinel     │───►│ Coolify Core │──► Notifications│
│  │ (metrics     │    │ (dashboard,  │    (Slack,      │
│  │  collection) │    │  alerts)     │     Discord,    │
│  └──────────────┘    └──────┬───────┘     Email...)   │
│                             │                         │
│  ┌──────────────┐    ┌──────┴───────┐               │
│  │ App Containers│───►│ Log Drains   │──► External    │
│  │ (stdout/err)  │    │ (Axiom,      │    Services    │
│  └──────────────┘    │  Loki, etc.) │               │
│                      └──────────────┘               │
│                                                      │
│  ┌──────────────┐                                    │
│  │ Uptime Kuma  │ (optional, deployed as service)    │
│  │ (HTTP checks)│                                    │
│  └──────────────┘                                    │
└─────────────────────────────────────────────────────┘
```

## Coolify Sentinel

> **Honest scope.** Sentinel is a **lightweight metrics side-car**, not a full observability solution. It collects CPU/RAM/disk/network metrics and exposes them in the Coolify UI. It does **not** include log aggregation, distributed tracing, alerting beyond simple threshold notifications, or APM features. Coolify itself flags Sentinel as **experimental** in the docs (the feature page carries a CAUTION banner). Sentinel **does not** support Docker Compose deployments or Service Template deployments — only single-container managed apps. If you need real observability, layer on Grafana+Prometheus or an external APM (Datadog, New Relic) — see the log drains section below.

### What Sentinel Monitors

Sentinel runs as a Docker container (`coolify-sentinel`) on each managed server:

| Metric | Description | Collection Interval |
|--------|-------------|-------------------|
| **CPU Usage** | Per-container and server-wide CPU % | ~10 seconds |
| **Memory Usage** | Per-container and server-wide memory | ~10 seconds |
| **Disk Usage** | Server disk space used/available | ~60 seconds |
| **Network I/O** | Bytes in/out per container | ~10 seconds |
| **Container Status** | Running, stopped, restarting | Real-time (Docker events) |
| **Server Connectivity** | Server reachability from Coolify main | Heartbeat |

**Not covered by Sentinel:** request latency, error rates, distributed tracing, log search, custom application metrics, multi-server aggregated dashboards. For these, use the log drain integrations or external APM described later in this skill.

### Viewing Metrics

- **Coolify Dashboard → Server → Resources**: Real-time CPU, memory, disk charts
- **Application → Status**: Container-level resource usage
- **Server → Docker**: Container list with status and resource usage

### Alert Thresholds

Configure in **Settings → Notifications**:
- **Disk usage** threshold (default: alert at 80%)
- **Container down** alerts (when a managed container stops unexpectedly)
- **Server unreachable** alerts (when Sentinel loses heartbeat)
- **Deployment status** alerts (success/failure notifications)

## Notification Channels

### Supported Channels

| Channel | Configuration | Supported Events |
|---------|---------------|-----------------|
| **Email** | SMTP settings (host, port, user, pass, from address) | All |
| **Slack** | Webhook URL | All |
| **Discord** | Webhook URL | All |
| **Telegram** | Bot token + chat ID | All |
| **Custom Webhook** | URL + optional headers | All |

### Configuration Path

1. Navigate to **Settings → Notifications**
2. Select channel type
3. Configure credentials
4. Test the notification
5. Select which events trigger notifications

### Slack Setup

1. Create a Slack Incoming Webhook at `api.slack.com/messaging/webhooks`
2. Copy the webhook URL (format: `https://hooks.slack.com/services/T.../B.../xxx`)
3. Paste in **Coolify → Settings → Notifications → Slack → Webhook URL**
4. Test → Send test message
5. Select events: deployments, container status, server alerts

### Discord Setup

1. In Discord: Server Settings → Integrations → Webhooks → New Webhook
2. Copy the webhook URL
3. Paste in **Coolify → Settings → Notifications → Discord → Webhook URL**
4. Test and configure events

### Telegram Setup

1. Create a bot via `@BotFather` in Telegram → get the bot token
2. Start a chat with the bot or add it to a group
3. Get the chat ID (send a message, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`)
4. Configure in Coolify: **Bot Token** + **Chat ID**

## Log Drains

### Supported Destinations

| Destination | Type | What's Sent |
|-------------|------|------------|
| **Axiom** | SaaS | Container stdout/stderr, build logs |
| **New Relic** | SaaS | Container logs with metadata |
| **Highlight.io** | SaaS | Container logs |
| **Custom HTTP/Fluentd** | Self-hosted or SaaS | Raw log lines via HTTP POST |

### Axiom Configuration

1. Create an Axiom account and dataset
2. Generate an API token with ingest permissions
3. In Coolify: **Server → Log Drains → Axiom**
   - **API Key**: Your Axiom API token
   - **Dataset**: Target dataset name
4. Logs flow automatically from all containers on that server

### New Relic Configuration

1. Get your New Relic License Key (ingest key)
2. In Coolify: **Server → Log Drains → New Relic**
   - **License Key**: Your NR ingest key
   - **Base URI**: `https://log-api.newrelic.com/log/v1` (US) or `https://log-api.eu.newrelic.com/log/v1` (EU)

### Custom HTTP Drain

For Loki, FluentBit, Datadog, or any HTTP endpoint:

1. In Coolify: **Server → Log Drains → Custom**
   - **URL**: Your log ingestion endpoint
   - **Headers**: Any required auth headers (e.g., `Authorization: Bearer <TOKEN>`)

### Verifying Log Drains

After configuration:
1. Deploy an application (generates build + runtime logs)
2. Check the destination for incoming logs
3. If no logs appear within 2 minutes:
   - Check Sentinel is running: `docker ps | grep sentinel`
   - Check network connectivity from server to log destination
   - Verify credentials and endpoint URL

## Uptime Kuma Integration

### Deploying Uptime Kuma in Coolify

Uptime Kuma is deployed as a **Service** (one-click) in Coolify:

1. **New Resource → Service → Uptime Kuma**
2. Configure domain (e.g., `status.example.com`)
3. Deploy
4. Set up monitors for your applications

### Recommended Monitor Types

| Monitor Type | Use For | Configuration |
|-------------|---------|---------------|
| **HTTP(s)** | Web apps with health endpoints | URL: `https://app.example.com/healthz`, interval: 60s |
| **HTTP(s) - Keyword** | Verify specific response content | Check for "ok" or "healthy" in response body |
| **Docker Container** | Monitor container directly | Requires Docker socket access (add as Docker host) |
| **TCP Port** | Non-HTTP services (databases, Redis) | Host: container name, Port: service port |

### Health Check Endpoint Pattern

Expose a `/healthz` endpoint in every application:

```javascript
// Express.js
app.get('/healthz', async (req, res) => {
  // Check dependencies
  const dbOk = await checkDatabase();
  const redisOk = await checkRedis();

  if (dbOk && redisOk) {
    res.status(200).json({ status: 'ok', db: 'connected', redis: 'connected' });
  } else {
    res.status(503).json({ status: 'degraded', db: dbOk, redis: redisOk });
  }
});
```

```python
# FastAPI
@app.get("/healthz")
async def healthz():
    db_ok = await check_database()
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
```

### Wiring Uptime Kuma to Notifications

Uptime Kuma has its own notification system (separate from Coolify's):
- Configure Slack, Discord, Telegram, email, etc. in Uptime Kuma's notification settings
- Set up a status page for public visibility

## External Monitoring Integration

### Grafana + Prometheus Stack

For advanced monitoring, deploy a Prometheus + Grafana stack alongside Coolify:

1. Deploy **Prometheus** as a Docker Compose service in Coolify
2. Configure Prometheus to scrape Docker metrics via cAdvisor
3. Deploy **Grafana** as a service in Coolify
4. Add Prometheus as a Grafana data source
5. Import Docker/container monitoring dashboards

**cAdvisor setup** (container metrics for Prometheus). Pin the image to a reviewed release or digest before deployment. The example uses a versioned tag and still requires a current release check:
```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.52.1
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports:
      - "8081:8080"
```

### Datadog / New Relic APM

For application-level monitoring (APM, traces, not just logs):
1. Install the agent inside the application container via Dockerfile
2. Set the agent API key as a runtime environment variable
3. Configure the agent to send traces to the SaaS endpoint

This is application-specific, not Coolify-specific — follow the APM provider's Docker documentation.
