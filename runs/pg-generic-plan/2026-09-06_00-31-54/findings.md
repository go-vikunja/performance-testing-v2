# Findings: pg-generic-plan / 2026-09-06_00-31-54

```
run=2026-09-06_00-31-54 name=pg-generic-plan users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788647491000 to=1788648183000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788647491000&to=1788648183000
vikunja_version=v2.6.0-132-g4a7d927a
```

## Locust summary

- requests: 361366  failures: 0  rps: 583.7967534631673
- response time ms: p50 13  p95 32  p99 97  max 327.283503000217
- postgres: 6775705 statements = 18.8 per request, 0.66 ms DB exec + 0.60 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2901 | 40 | 38 | 80 |
| POST /projects [create] | 382 | 35 | 31 | 64 |
| POST /projects/{id}/tasks [create] | 2020 | 23 | 20 | 43 |
| PATCH /tasks/{id} [patch] | 2490 | 23 | 18 | 46 |
| GET /tasks [bot] | 6143 | 23 | 18 | 41 |
| GET /projects | 4922 | 23 | 19 | 49 |
| GET /tasks [home] | 10992 | 22 | 17 | 47 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3925 | 20 | 17 | 37 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 774 | 20 | 16 | 40 |
| GET /tasks/{id} | 4816 | 18 | 15 | 34 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
