# Findings: big-cap20000 / 2026-09-06_16-08-58

```
run=2026-09-06_16-08-58 name=big-cap20000 users=20000 spawn_rate=125 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788703715000 to=1788704406000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788703715000&to=1788704406000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 2048048  failures: 22  rps: 3298.856516292575
- response time ms: p50 150  p95 640  p99 980  max 3369.121227999983
- postgres: 26255484 statements = 12.8 per request, 0.45 ms DB exec + 0.13 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| GET /tasks [bot] | 32131 | 296 | 240 | 750 |
| GET /projects [bot] | 96714 | 290 | 230 | 750 |
| GET /projects/{id}/tasks [bot] | 246853 | 288 | 230 | 740 |
| GET /tasks/{id} [bot] | 696748 | 287 | 230 | 740 |
| PATCH /tasks/{id} [patch] | 15040 | 265 | 210 | 720 |
| POST /projects [create] | 2504 | 187 | 140 | 490 |
| POST /projects/{id}/tasks [create] | 12648 | 166 | 110 | 490 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 5105 | 160 | 110 | 470 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 24974 | 160 | 110 | 470 |
| GET /tasks/{id} | 30222 | 157 | 100 | 470 |

### Failures

- 15x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 7x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
