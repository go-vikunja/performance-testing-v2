# Findings: cap6000 / 2026-09-06_01-51-04

```
run=2026-09-06_01-51-04 name=cap6000 users=6000 spawn_rate=50 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788652234000 to=1788652926000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788652234000&to=1788652926000
vikunja_version=v2.6.0-132-g4a7d927a
```

## Locust summary

- requests: 710993  failures: 3  rps: 1149.1351835859462
- response time ms: p50 24  p95 98  p99 200  max 1390.0683730007586
- postgres: 13244551 statements = 18.6 per request, 0.96 ms DB exec + 0.70 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 749 | 71 | 64 | 120 |
| POST /login | 5808 | 70 | 61 | 140 |
| GET /tasks [bot] | 12228 | 50 | 35 | 120 |
| PATCH /tasks/{id} [patch] | 4927 | 47 | 37 | 110 |
| GET /tasks/{id} [bot] | 262820 | 45 | 30 | 120 |
| GET /projects/{id}/tasks [bot] | 93345 | 43 | 27 | 110 |
| GET /projects [bot] | 36465 | 43 | 27 | 110 |
| GET /tasks [home] | 21676 | 42 | 36 | 82 |
| POST /projects/{id}/tasks [create] | 3965 | 41 | 36 | 78 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 7886 | 39 | 33 | 75 |

### Failures

- 1x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 2x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
