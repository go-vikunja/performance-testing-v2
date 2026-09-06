# Findings: combined-profile / 2026-09-06_11-21-58

```
run=2026-09-06_11-21-58 name=combined-profile users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788686495000 to=1788687187000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788686495000&to=1788687187000
vikunja_version=v2.6.0-149-gab2d3224
```

## Locust summary

- requests: 360697  failures: 0  rps: 583.6879188710371
- response time ms: p50 11  p95 22  p99 39  max 1030.4029160033679
- postgres: 6506084 statements = 18.0 per request, 0.49 ms DB exec + 0.15 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2935 | 36 | 35 | 58 |
| POST /projects [create] | 402 | 28 | 26 | 41 |
| GET /projects | 4934 | 18 | 17 | 36 |
| GET /tasks [bot] | 6260 | 18 | 17 | 25 |
| GET /tasks [home] | 10817 | 18 | 15 | 32 |
| POST /projects/{id}/tasks [create] | 1971 | 18 | 16 | 26 |
| PATCH /tasks/{id} [patch] | 2416 | 17 | 16 | 32 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4042 | 16 | 15 | 24 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 851 | 15 | 14 | 22 |
| POST /tasks/{id}/labels [add] | 813 | 14 | 13 | 21 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
