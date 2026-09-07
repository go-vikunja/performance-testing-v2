# Findings: db23-cap12000 / 2026-09-06_15-28-58

```
run=2026-09-06_15-28-58 name=db23-cap12000 users=12000 spawn_rate=100 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=8"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx33
from=1788701314000 to=1788702006000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788701314000&to=1788702006000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 1443415  failures: 5  rps: 2332.2609737874336
- response time ms: p50 9  p95 73  p99 190  max 1057.8185690000055
- postgres: 18955482 statements = 13.1 per request, 0.67 ms DB exec + 0.18 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 11736 | 61 | 43 | 170 |
| POST /projects [create] | 1583 | 48 | 34 | 120 |
| GET /tasks [home] | 43669 | 43 | 22 | 130 |
| GET /projects | 19679 | 38 | 22 | 120 |
| GET /labels | 19679 | 36 | 18 | 130 |
| PATCH /tasks/{id} [patch] | 9496 | 30 | 16 | 110 |
| POST /projects/{id}/tasks [create] | 8004 | 29 | 18 | 87 |
| GET /tasks [bot] | 24807 | 28 | 16 | 90 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 3113 | 27 | 17 | 85 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 16067 | 26 | 16 | 78 |

### Failures

- 5x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
