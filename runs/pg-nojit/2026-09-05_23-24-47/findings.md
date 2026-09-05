# Findings: pg-nojit / 2026-09-05_23-24-47

```
run=2026-09-05_23-24-47 name=pg-nojit users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788643464000 to=1788644155000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788643464000&to=1788644155000
vikunja_version=v2.6.0-119-g2c22cfb6
```

## Locust summary

- requests: 361597  failures: 1  rps: 586.6683256234438
- response time ms: p50 17  p95 50  p99 94  max 476.8593829994643
- postgres: 4703100 statements = 13.0 per request, 0.69 ms DB exec + 1.71 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 425 | 66 | 55 | 140 |
| PATCH /tasks/{id} [patch] | 2356 | 42 | 34 | 92 |
| POST /projects/{id}/tasks [create] | 2066 | 40 | 33 | 83 |
| GET /tasks [home] | 10809 | 38 | 30 | 81 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3954 | 36 | 30 | 73 |
| POST /login | 6652 | 34 | 31 | 82 |
| GET /tasks/{id} | 4769 | 33 | 27 | 71 |
| GET /projects | 4937 | 32 | 28 | 70 |
| GET /projects/{id}/views/{view}/tasks [list] | 15066 | 30 | 24 | 61 |
| GET /tasks [bot] | 6243 | 30 | 25 | 57 |

### Failures

- 1x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
