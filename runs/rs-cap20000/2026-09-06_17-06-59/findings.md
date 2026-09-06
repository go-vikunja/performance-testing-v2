# Findings: rs-cap20000 / 2026-09-06_17-06-59

```
run=2026-09-06_17-06-59 name=rs-cap20000 users=20000 spawn_rate=125 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788707196000 to=1788707887000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788707196000&to=1788707887000
vikunja_version=v2.6.0-163-gf1c764e7
```

## Locust summary

- requests: 2315352  failures: 31  rps: 3737.1526526254297
- response time ms: p50 15  p95 54  p99 94  max 1153.8718040001186
- postgres: 24313279 statements = 10.5 per request, 0.44 ms DB exec + 0.17 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 2575 | 79 | 66 | 170 |
| POST /login | 19573 | 45 | 44 | 75 |
| POST /projects/{id}/tasks [create] | 12746 | 44 | 36 | 100 |
| GET /tasks [home] | 70408 | 43 | 37 | 99 |
| PATCH /tasks/{id} [patch] | 15525 | 39 | 29 | 100 |
| GET /projects | 32022 | 37 | 31 | 87 |
| GET /tasks [bot] | 39946 | 35 | 30 | 76 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 25645 | 35 | 29 | 77 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 5149 | 31 | 25 | 72 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 3783 | 30 | 22 | 79 |

### Failures

- 1x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 30x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
