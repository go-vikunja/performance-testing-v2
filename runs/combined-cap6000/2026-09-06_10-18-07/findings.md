# Findings: combined-cap6000 / 2026-09-06_10-18-07

```
run=2026-09-06_10-18-07 name=combined-cap6000 users=6000 spawn_rate=50 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788682664000 to=1788683356000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788682664000&to=1788683356000
vikunja_version=v2.6.0-144-ge8da5b74
```

## Locust summary

- requests: 718323  failures: 0  rps: 1163.6942750856322
- response time ms: p50 15  p95 56  p99 110  max 1432.7546040003654
- postgres: 13055246 statements = 18.2 per request, 0.47 ms DB exec + 0.15 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 5858 | 64 | 59 | 110 |
| POST /projects [create] | 793 | 40 | 33 | 79 |
| GET /projects | 9849 | 33 | 26 | 100 |
| GET /tasks [home] | 21879 | 31 | 23 | 66 |
| GET /tasks [bot] | 12408 | 29 | 22 | 64 |
| PATCH /tasks/{id} [patch] | 4661 | 29 | 22 | 66 |
| POST /user/token/refresh | 11756 | 28 | 16 | 64 |
| GET /user | 9849 | 28 | 14 | 120 |
| POST /projects/{id}/tasks [create] | 3903 | 27 | 21 | 57 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 7882 | 25 | 19 | 51 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
