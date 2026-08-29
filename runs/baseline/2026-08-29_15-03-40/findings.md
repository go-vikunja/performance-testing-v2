# Findings: baseline / 2026-08-29_15-03-40

```
run=2026-08-29_15-03-40 name=baseline users=1500 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788008594000 to=1788009285000
grafana_url=http://178.104.196.14:3000/d/perf-overview/perf-overview?from=1788008594000&to=1788009285000
vikunja_version=v2.5.0-249-gc0ebf473
```

## Locust summary

- requests: 180589  failures: 0  rps: 301.0490196484262
- response time ms: p50 13  p95 1100  p99 6100  max 31040.450683999552
- postgres: 2683292 statements = 14.9 per request, 1.56 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 3331 | 3629 | 1900 | 13000 |
| GET /projects | 2474 | 1441 | 400 | 6100 |
| GET /user | 2474 | 1327 | 120 | 6600 |
| GET /labels | 2474 | 1309 | 450 | 5800 |
| GET /tasks [home] | 5448 | 745 | 24 | 4000 |
| PATCH /tasks/{id} [patch] | 1230 | 286 | 22 | 1000 |
| GET /projects/{id}/views/{view}/tasks [list] | 7377 | 255 | 18 | 1500 |
| GET /tasks/{id} | 2380 | 248 | 19 | 1100 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 2019 | 235 | 23 | 1300 |
| POST /tasks/{id}/labels [add] | 388 | 219 | 14 | 1400 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
