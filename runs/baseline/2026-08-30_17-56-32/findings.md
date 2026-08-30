# Findings: baseline / 2026-08-30_17-56-32

```
run=2026-08-30_17-56-32 name=baseline users=500 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788105366000 to=1788106056000
grafana_url=http://178.104.207.216:3000/d/perf-overview/perf-overview?from=1788105366000&to=1788106056000
vikunja_version=v2.5.0-345-g5694ef63
```

## Locust summary

- requests: 63993  failures: 0  rps: 103.53876189458512
- response time ms: p50 20  p95 170  p99 2800  max 13905.668763999984
- postgres: 835240 statements = 13.1 per request, 1.39 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 1125 | 2046 | 1500 | 6600 |
| GET /projects | 839 | 805 | 130 | 2900 |
| GET /labels | 839 | 615 | 52 | 2800 |
| GET /user | 839 | 587 | 41 | 2500 |
| GET /tasks [home] | 1922 | 416 | 31 | 2600 |
| POST /projects/{id}/tasks [create] | 358 | 127 | 30 | 47 |
| POST /projects [create] | 72 | 112 | 62 | 82 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 102 | 109 | 29 | 54 |
| PATCH /tasks/{id} [patch] | 445 | 95 | 36 | 65 |
| POST /tasks/{id}/labels [add] | 130 | 91 | 23 | 36 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
