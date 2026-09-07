# Findings: cap14000 / 2026-09-06_15-01-21

```
run=2026-09-06_15-01-21 name=cap14000 users=14000 spawn_rate=100 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=8"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx33
from=1788699659000 to=1788700350000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788699659000&to=1788700350000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 1661422  failures: 8  rps: 2685.602080166004
- response time ms: p50 6  p95 40  p99 98  max 1228.0797169999005
- postgres: 21833603 statements = 13.1 per request, 0.27 ms DB exec + 0.09 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 13671 | 60 | 51 | 140 |
| POST /projects [create] | 1878 | 28 | 21 | 70 |
| GET /projects | 22680 | 21 | 16 | 59 |
| GET /tasks [home] | 49909 | 21 | 14 | 52 |
| GET /tasks [bot] | 28660 | 17 | 11 | 52 |
| PATCH /tasks/{id} [patch] | 10981 | 17 | 10 | 57 |
| POST /projects/{id}/tasks [create] | 9171 | 16 | 11 | 46 |
| GET /labels | 22680 | 15 | 8 | 49 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 18404 | 15 | 11 | 37 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 3687 | 14 | 11 | 36 |

### Failures

- 8x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
