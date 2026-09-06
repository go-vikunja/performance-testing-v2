# Findings: partial-index / 2026-09-06_02-08-51

```
run=2026-09-06_02-08-51 name=partial-index users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788653308000 to=1788653999000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788653308000&to=1788653999000
vikunja_version=v2.6.0-132-g4a7d927a
```

## Locust summary

- requests: 363210  failures: 0  rps: 588.8983457812047
- response time ms: p50 13  p95 24  p99 41  max 1036.2716090003232
- postgres: 6769521 statements = 18.6 per request, 0.52 ms DB exec + 0.48 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2941 | 35 | 36 | 55 |
| POST /projects [create] | 371 | 33 | 32 | 45 |
| PATCH /tasks/{id} [patch] | 2365 | 20 | 18 | 37 |
| GET /projects | 4940 | 20 | 17 | 40 |
| POST /projects/{id}/tasks [create] | 1943 | 19 | 18 | 28 |
| GET /tasks [home] | 11058 | 19 | 17 | 34 |
| GET /tasks [bot] | 6366 | 19 | 17 | 26 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4013 | 17 | 16 | 26 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 777 | 17 | 15 | 25 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 605 | 15 | 16 | 28 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
