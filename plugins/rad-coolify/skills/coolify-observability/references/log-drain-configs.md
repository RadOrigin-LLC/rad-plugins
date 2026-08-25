# Log Drain Configuration Reference

## Live-change gate

Before changing a log drain or sending data to an external destination, confirm the exact instance and resource, state the action and expected effect, and require user acceptance. Use a protected environment or manual approval for CI and stop without approval.

## How Log Drains Work in Coolify

Coolify's log drain system captures container stdout/stderr and forwards them to external services. The drain runs at the **server level** — all containers on that server send logs to the configured drain.

## Axiom

### Configuration

| Field | Value |
|-------|-------|
| **API Key** | Create at axiom.co → Settings → API Tokens → New Token (Ingest permission) |
| **Dataset** | Name of the target dataset (create in Axiom first) |

### What Gets Sent

Each log line includes:
- `timestamp` — when the log was generated
- `container_name` — Coolify container name
- `message` — the log line content
- `source` — `stdout` or `stderr`
- `host` — server hostname

### Axiom Query Example

```apl
# Find errors from a specific app in the last hour
['coolify-logs']
| where container_name == "app-xxxx"
| where message contains "error" or message contains "Error"
| sort by _time desc
| take 100
```

### Verification

```bash
# Check Axiom is receiving logs
# In Axiom UI: Datasets → your dataset → Stream tab
# Should see live log entries within 30 seconds of any container output
```

## New Relic

### Configuration

| Field | Value |
|-------|-------|
| **License Key** | From New Relic One → Account Settings → API Keys → Ingest License Key |
| **Base URI** | US: `https://log-api.newrelic.com/log/v1` |
|             | EU: `https://log-api.eu.newrelic.com/log/v1` |

### What Gets Sent

New Relic log format:
```json
{
  "timestamp": 1704067200000,
  "message": "Server started on port 3000",
  "attributes": {
    "container_name": "app-xxxx",
    "hostname": "coolify-server-1",
    "source": "stdout"
  }
}
```

### New Relic Query (NRQL)

```sql
SELECT * FROM Log
WHERE container_name = 'app-xxxx'
AND message LIKE '%error%'
SINCE 1 hour ago
```

## Highlight.io

### Configuration

| Field | Value |
|-------|-------|
| **Project ID** | From Highlight dashboard → Settings → Project ID |

### Notes
- Highlight provides both logging and session replay
- Log drain sends container logs only (not browser sessions)
- Useful if already using Highlight for frontend monitoring

## Custom HTTP (Loki, FluentBit, Logstash, Datadog)

### Loki (via Promtail or direct push)

Coolify's custom HTTP drain sends logs as HTTP POST. For Loki:

| Field | Value |
|-------|-------|
| **URL** | `http://loki:3100/loki/api/v1/push` (if Loki is on the same server) |
| **Headers** | `Content-Type: application/json` |

**Note**: Loki expects a specific JSON format. You may need a FluentBit or Promtail intermediary to transform the log format.

### Direct Loki Push (via FluentBit sidecar)

For better Loki integration, deploy FluentBit as a Docker container:

```yaml
# docker-compose.yml for FluentBit log shipper
services:
  fluentbit:
    image: fluent/fluent-bit:3.1.10
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
    depends_on:
      - loki

  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki

volumes:
  loki-data:
```

**fluent-bit.conf**:
```ini
[SERVICE]
    Flush        5
    Log_Level    info

[INPUT]
    Name         docker
    Tag          docker.*
    Docker_Mode  On

[FILTER]
    Name         modify
    Match        docker.*
    Add          hostname ${HOSTNAME}

[OUTPUT]
    Name         loki
    Match        docker.*
    Host         loki
    Port         3100
    Labels       job=coolify,container_name=$container_name
    Remove_Keys  container_id,container_name
```

### Datadog

| Field | Value |
|-------|-------|
| **URL** | `https://http-intake.logs.datadoghq.com/api/v2/logs` |
| **Headers** | `DD-API-KEY: <YOUR_DATADOG_API_KEY>`, `Content-Type: application/json` |

### Logstash

| Field | Value |
|-------|-------|
| **URL** | `http://logstash:5044` (or wherever your Logstash HTTP input is) |
| **Headers** | `Content-Type: application/json` |

## Log Filtering and Sampling

Coolify's built-in log drain does NOT support filtering or sampling. All container logs are forwarded.

### Workarounds

1. **Application-level**: Configure your app to only log at appropriate levels (INFO, WARN, ERROR in production — not DEBUG)
2. **FluentBit intermediary**: Deploy FluentBit between containers and the drain to filter/sample
3. **Destination-side**: Use the log platform's filtering (Axiom filters, Loki label selectors, etc.)

### Cost Control for Paid Log Services

| Strategy | Implementation |
|----------|---------------|
| Log only WARN+ in production | Set `LOG_LEVEL=warn` in app env vars |
| Exclude health check logs | Configure app to not log `/healthz` requests |
| Sample verbose endpoints | Application-level sampling (log 1 in 10 requests) |
| Use structured logging | JSON logs are easier to filter downstream |
| Set retention limits | Configure in the log platform (e.g., 7 days for Axiom free tier) |

## Verification Checklist

After configuring any log drain:

- [ ] Deploy or restart an application (generates logs)
- [ ] Check the destination for incoming log entries within 2 minutes
- [ ] Verify log entries contain container name and timestamp
- [ ] Trigger an error in an app and verify it appears in the drain
- [ ] Check that build logs also appear (not just runtime logs)
- [ ] Verify Sentinel is running: `docker ps | grep sentinel`
