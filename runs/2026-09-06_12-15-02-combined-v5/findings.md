# Findings: combined-v5 / 2026-09-06_12-15-02

```
run=2026-09-06_12-15-02 name=combined-v5 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788689679000 to=1788690370000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788689679000&to=1788690370000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 363207  failures: 0  rps: 588.3310650179852
- response time ms: p50 9  p95 21  p99 38  max 1018.6117429984733
- postgres: 4783951 statements = 13.2 per request, 0.55 ms DB exec + 0.18 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2916 | 38 | 37 | 59 |
| POST /projects [create] | 393 | 31 | 29 | 43 |
| GET /projects | 4914 | 19 | 17 | 39 |
| GET /tasks [home] | 10978 | 18 | 16 | 30 |
| POST /projects/{id}/tasks [create] | 2012 | 17 | 16 | 25 |
| GET /tasks [bot] | 6276 | 17 | 16 | 23 |
| PATCH /tasks/{id} [patch] | 2400 | 16 | 15 | 30 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3989 | 16 | 15 | 23 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 815 | 15 | 15 | 23 |
| POST /tasks/{id}/labels [add] | 785 | 14 | 13 | 21 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
