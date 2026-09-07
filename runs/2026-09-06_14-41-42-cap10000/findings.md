# Findings: cap10000 / 2026-09-06_14-41-42

```
run=2026-09-06_14-41-42 name=cap10000 users=10000 spawn_rate=80 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx33
from=1788698478000 to=1788699170000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788698478000&to=1788699170000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 1205760  failures: 2  rps: 1950.8552943854563
- response time ms: p50 6  p95 21  p99 64  max 1033.5523050000006
- postgres: 15855250 statements = 13.1 per request, 0.23 ms DB exec + 0.08 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 9802 | 55 | 51 | 110 |
| POST /projects [create] | 1331 | 21 | 18 | 34 |
| GET /projects | 16345 | 16 | 14 | 37 |
| GET /tasks [home] | 36152 | 16 | 12 | 35 |
| GET /tasks [bot] | 20759 | 13 | 10 | 17 |
| PATCH /tasks/{id} [patch] | 7959 | 12 | 9 | 27 |
| POST /projects/{id}/tasks [create] | 6614 | 12 | 10 | 27 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 13192 | 11 | 10 | 21 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 2634 | 11 | 9 | 21 |
| GET /labels | 16345 | 10 | 7 | 26 |

### Failures

- 2x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
