# Findings: conn-lifetime / 2026-09-06_00-45-48

```
run=2026-09-06_00-45-48 name=conn-lifetime users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788648325000 to=1788649016000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788648325000&to=1788649016000
vikunja_version=v2.6.0-132-g4a7d927a
```

## Locust summary

- requests: 361125  failures: 0  rps: 583.6364976699339
- response time ms: p50 13  p95 24  p99 43  max 1036.7209920004825
- postgres: 6774198 statements = 18.8 per request, 0.62 ms DB exec + 0.50 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2941 | 37 | 36 | 57 |
| POST /projects [create] | 416 | 33 | 32 | 48 |
| PATCH /tasks/{id} [patch] | 2364 | 20 | 18 | 39 |
| GET /projects | 4926 | 20 | 18 | 40 |
| GET /tasks [home] | 11055 | 19 | 17 | 34 |
| POST /projects/{id}/tasks [create] | 1952 | 19 | 17 | 30 |
| GET /tasks [bot] | 6207 | 19 | 17 | 27 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3895 | 18 | 16 | 26 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 848 | 17 | 16 | 24 |
| GET /tasks/{id} | 4865 | 16 | 14 | 25 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
