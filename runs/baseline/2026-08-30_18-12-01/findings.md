# Findings: baseline / 2026-08-30_18-12-01

```
run=2026-08-30_18-12-01 name=baseline users=1500 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788106295000 to=1788106985000
grafana_url=http://178.104.207.216:3000/d/perf-overview/perf-overview?from=1788106295000&to=1788106985000
vikunja_version=v2.5.0-345-g5694ef63
```

## Locust summary

- requests: 177638  failures: 0  rps: 287.6652164393559
- response time ms: p50 15  p95 1000  p99 8600  max 47480.51663900014
- postgres: 2298375 statements = 12.9 per request, 1.00 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 3281 | 5605 | 2900 | 20000 |
| GET /projects | 2424 | 2018 | 440 | 8800 |
| GET /user | 2424 | 1831 | 220 | 8900 |
| GET /labels | 2424 | 1668 | 220 | 7900 |
| GET /tasks [home] | 5367 | 958 | 25 | 5500 |
| PATCH /tasks/{id} [patch] | 1204 | 387 | 26 | 1100 |
| POST /projects [create] | 230 | 386 | 45 | 1600 |
| POST /tasks/{id}/labels [add] | 386 | 356 | 18 | 2300 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 294 | 353 | 21 | 1200 |
| PUT /tasks/{id}/position | 558 | 292 | 8 | 800 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
