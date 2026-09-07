# Findings: cap9000 / 2026-09-06_13-57-32

```
run=2026-09-06_13-57-32 name=cap9000 users=9000 spawn_rate=75 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788695829000 to=1788696520000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788695829000&to=1788696520000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 1077719  failures: 6  rps: 1747.4470884447314
- response time ms: p50 11  p95 89  p99 180  max 1007.198769999377
- postgres: 14191514 statements = 13.2 per request, 0.45 ms DB exec + 0.14 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 8840 | 85 | 70 | 200 |
| POST /projects [create] | 1211 | 49 | 36 | 120 |
| PATCH /tasks/{id} [patch] | 7443 | 35 | 19 | 110 |
| GET /projects | 14734 | 35 | 24 | 100 |
| GET /tasks [home] | 32581 | 35 | 24 | 90 |
| GET /tasks [bot] | 18588 | 34 | 19 | 110 |
| POST /projects/{id}/tasks [create] | 5957 | 31 | 20 | 83 |
| GET /projects [bot] | 55664 | 29 | 14 | 100 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 11942 | 28 | 18 | 73 |
| GET /labels | 14734 | 28 | 15 | 90 |

### Failures

- 2x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 4x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
