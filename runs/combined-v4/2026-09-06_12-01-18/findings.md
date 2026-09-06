# Findings: combined-v4 / 2026-09-06_12-01-18

```
run=2026-09-06_12-01-18 name=combined-v4 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788688855000 to=1788689546000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788688855000&to=1788689546000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 362661  failures: 1  rps: 585.6923093707971
- response time ms: p50 10  p95 21  p99 39  max 1030.7939850026742
- postgres: 5284906 statements = 14.6 per request, 0.55 ms DB exec + 0.17 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2933 | 38 | 38 | 60 |
| POST /projects [create] | 394 | 30 | 28 | 44 |
| GET /projects | 4940 | 19 | 17 | 39 |
| GET /tasks [home] | 10921 | 18 | 16 | 30 |
| PATCH /tasks/{id} [patch] | 2401 | 18 | 16 | 33 |
| POST /projects/{id}/tasks [create] | 2133 | 18 | 16 | 25 |
| GET /tasks [bot] | 6206 | 17 | 16 | 23 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3956 | 17 | 16 | 24 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 735 | 16 | 15 | 23 |
| POST /tasks/{id}/labels [add] | 796 | 15 | 14 | 22 |

### Failures

- 1x POST /user/token/refresh: LocustBadStatusCode(code=401)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
