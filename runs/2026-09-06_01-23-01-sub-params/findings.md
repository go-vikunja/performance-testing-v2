# Findings: sub-params / 2026-09-06_01-23-01

```
run=2026-09-06_01-23-01 name=sub-params users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788650551000 to=1788651242000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788650551000&to=1788651242000
vikunja_version=v2.6.0-141-g8ba3bbdf
```

## Locust summary

- requests: 359203  failures: 1  rps: 580.8639510185454
- response time ms: p50 20  p95 55  p99 92  max 1043.3770590007043
- postgres: 6705604 statements = 18.7 per request, 0.84 ms DB exec + 0.15 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2925 | 44 | 43 | 76 |
| POST /projects [create] | 381 | 43 | 37 | 89 |
| GET /tasks [bot] | 6198 | 37 | 30 | 75 |
| GET /projects/{id}/tasks [bot] | 47595 | 30 | 24 | 64 |
| GET /projects [bot] | 18414 | 30 | 24 | 61 |
| GET /tasks/{id} [bot] | 133063 | 29 | 23 | 63 |
| PATCH /tasks/{id} [patch] | 2432 | 29 | 23 | 65 |
| POST /projects/{id}/tasks [create] | 1900 | 28 | 22 | 59 |
| GET /tasks [home] | 10987 | 27 | 22 | 56 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3896 | 26 | 22 | 54 |

### Failures

- 1x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
