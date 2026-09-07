# Findings: smoke / 2026-08-29_14-58-47

```
run=2026-08-29_14-58-47 name=smoke users=20 spawn_rate=10 duration=60s classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788008300000 to=1788008451000
grafana_url=http://178.104.196.14:3000/d/perf-overview/perf-overview?from=1788008300000&to=1788008451000
vikunja_version=v2.5.0-249-gc0ebf473
```

## Locust summary

- requests: 415  failures: 0  rps: 6.996335344549717
- response time ms: p50 18  p95 160  p99 360  max 369.012326000302
- postgres: 7780 statements = 18.7 per request, 9.84 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 29 | 275 | 310 | 370 |
| GET /projects | 17 | 71 | 50 | 120 |
| GET /tasks [bot] | 5 | 55 | 30 | 160 |
| POST /projects [create] | 1 | 50 | 50 | 50 |
| GET /labels | 17 | 38 | 41 | 57 |
| POST /projects/{id}/tasks [create] | 3 | 29 | 25 | 39 |
| GET /tasks [home] | 20 | 26 | 26 | 45 |
| PATCH /tasks/{id} [patch] | 2 | 25 | 27 | 27 |
| POST /tasks/{id}/labels [add] | 2 | 23 | 26 | 26 |
| GET /tasks/{id} | 4 | 23 | 24 | 30 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
