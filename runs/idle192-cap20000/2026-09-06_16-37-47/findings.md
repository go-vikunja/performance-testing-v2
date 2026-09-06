# Findings: idle192-cap20000 / 2026-09-06_16-37-47

```
run=2026-09-06_16-37-47 name=idle192-cap20000 users=20000 spawn_rate=125 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788705445000 to=1788706136000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788705445000&to=1788706136000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 2294156  failures: 34  rps: 3694.6368419654323
- response time ms: p50 29  p95 82  p99 140  max 1172.6542549999976
- postgres: 30097157 statements = 13.1 per request, 0.43 ms DB exec + 0.15 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 2489 | 111 | 110 | 190 |
| POST /projects/{id}/tasks [create] | 12701 | 63 | 60 | 110 |
| PATCH /tasks/{id} [patch] | 15243 | 61 | 50 | 150 |
| GET /tasks [bot] | 39212 | 58 | 54 | 110 |
| GET /tasks [home] | 70500 | 57 | 53 | 100 |
| POST /login | 19492 | 53 | 43 | 120 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 25715 | 52 | 49 | 98 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 5174 | 50 | 46 | 96 |
| GET /projects | 32165 | 47 | 42 | 92 |
| GET /projects [bot] | 116998 | 46 | 42 | 92 |

### Failures

- 2x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 32x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
