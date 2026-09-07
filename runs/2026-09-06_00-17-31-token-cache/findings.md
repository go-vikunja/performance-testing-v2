# Findings: token-cache / 2026-09-06_00-17-31

```
run=2026-09-06_00-17-31 name=token-cache users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788646628000 to=1788647319000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788646628000&to=1788647319000
vikunja_version=v2.6.0-132-g4a7d927a
```

## Locust summary

- requests: 361457  failures: 1  rps: 583.3840275199178
- response time ms: p50 13  p95 37  p99 100  max 358.59433000041463
- postgres: 6767032 statements = 18.7 per request, 0.67 ms DB exec + 0.82 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2956 | 40 | 37 | 77 |
| POST /projects [create] | 394 | 38 | 32 | 71 |
| POST /projects/{id}/tasks [create] | 1976 | 25 | 20 | 57 |
| PATCH /tasks/{id} [patch] | 2407 | 25 | 19 | 53 |
| GET /tasks [bot] | 6204 | 24 | 19 | 53 |
| GET /projects | 4892 | 24 | 20 | 56 |
| GET /tasks [home] | 10850 | 23 | 18 | 54 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3985 | 22 | 18 | 46 |
| GET /tasks/{id} | 4747 | 20 | 15 | 45 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 589 | 19 | 17 | 42 |

### Failures

- 1x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
