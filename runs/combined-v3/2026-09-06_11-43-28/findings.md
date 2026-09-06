# Findings: combined-v3 / 2026-09-06_11-43-28

```
run=2026-09-06_11-43-28 name=combined-v3 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788687785000 to=1788688476000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788687785000&to=1788688476000
vikunja_version=v2.6.0-149-gab2d3224
```

## Locust summary

- requests: 363893  failures: 0  rps: 592.8910548740263
- response time ms: p50 10  p95 21  p99 37  max 433.7044700005208
- postgres: 5295031 statements = 14.6 per request, 0.53 ms DB exec + 0.17 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2973 | 36 | 35 | 57 |
| POST /projects [create] | 413 | 29 | 28 | 40 |
| GET /projects | 4910 | 19 | 17 | 38 |
| PATCH /tasks/{id} [patch] | 2472 | 18 | 16 | 34 |
| GET /tasks [home] | 10900 | 18 | 16 | 30 |
| POST /projects/{id}/tasks [create] | 2015 | 18 | 16 | 25 |
| GET /tasks [bot] | 6245 | 17 | 16 | 23 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3992 | 17 | 16 | 24 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 825 | 15 | 15 | 23 |
| POST /tasks/{id}/labels [add] | 810 | 15 | 14 | 24 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
