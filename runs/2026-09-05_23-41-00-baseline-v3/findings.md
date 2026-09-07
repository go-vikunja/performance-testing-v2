# Findings: baseline-v3 / 2026-09-05_23-41-00

```
run=2026-09-05_23-41-00 name=baseline-v3 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788644436000 to=1788645128000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788644436000&to=1788645128000
vikunja_version=v2.6.0-119-g2c22cfb6
```

## Locust summary

- requests: 346229  failures: 4  rps: 563.1524520817989
- response time ms: p50 65  p95 200  p99 350  max 1656.9675259997894
- postgres: 6390395 statements = 18.5 per request, 0.93 ms DB exec + 2.39 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 447 | 148 | 150 | 220 |
| GET /tasks [bot] | 5754 | 120 | 100 | 250 |
| GET /tasks/{id} [bot] | 124754 | 109 | 92 | 240 |
| GET /projects/{id}/tasks [bot] | 44204 | 109 | 90 | 240 |
| PATCH /tasks/{id} [patch] | 2359 | 104 | 93 | 210 |
| GET /projects [bot] | 17103 | 103 | 85 | 230 |
| POST /projects/{id}/tasks [create] | 2082 | 94 | 91 | 150 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4059 | 82 | 78 | 140 |
| GET /tasks/{id} | 4816 | 75 | 71 | 130 |
| GET /tasks [home] | 10963 | 71 | 66 | 130 |

### Failures

- 4x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
