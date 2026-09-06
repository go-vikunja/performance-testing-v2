# Findings: combined / 2026-09-06_10-05-12

```
run=2026-09-06_10-05-12 name=combined users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788681889000 to=1788682580000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788681889000&to=1788682580000
vikunja_version=v2.6.0-144-ge8da5b74
```

## Locust summary

- requests: 362972  failures: 2  rps: 588.4771899006944
- response time ms: p50 12  p95 22  p99 40  max 1041.440421999141
- postgres: 6594572 statements = 18.2 per request, 0.53 ms DB exec + 0.14 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2953 | 36 | 36 | 57 |
| POST /projects [create] | 355 | 28 | 26 | 39 |
| GET /projects | 4918 | 19 | 17 | 39 |
| GET /tasks [bot] | 6317 | 19 | 17 | 26 |
| GET /tasks [home] | 10998 | 18 | 15 | 32 |
| PATCH /tasks/{id} [patch] | 2307 | 18 | 16 | 33 |
| POST /projects/{id}/tasks [create] | 1935 | 17 | 16 | 26 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3967 | 16 | 15 | 24 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 807 | 15 | 14 | 23 |
| POST /tasks/{id}/labels [add] | 770 | 14 | 13 | 24 |

### Failures

- 2x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
