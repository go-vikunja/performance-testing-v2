# Findings: pool192-cap20000 / 2026-09-06_16-23-33

```
run=2026-09-06_16-23-33 name=pool192-cap20000 users=20000 spawn_rate=125 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788704590000 to=1788705281000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788704590000&to=1788705281000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 2247022  failures: 39  rps: 3627.4033339045022
- response time ms: p50 57  p95 160  p99 260  max 1328.6536729999625
- postgres: 29423985 statements = 13.1 per request, 0.58 ms DB exec + 0.75 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 2600 | 188 | 190 | 270 |
| POST /projects/{id}/tasks [create] | 12815 | 120 | 120 | 200 |
| GET /tasks [bot] | 37571 | 113 | 100 | 210 |
| PATCH /tasks/{id} [patch] | 15404 | 112 | 97 | 250 |
| POST /login | 19391 | 108 | 90 | 250 |
| GET /tasks [home] | 69990 | 97 | 90 | 170 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 25359 | 96 | 93 | 160 |
| GET /projects [bot] | 113968 | 92 | 82 | 180 |
| GET /tasks/{id} | 30263 | 82 | 76 | 150 |
| GET /projects/{id}/tasks [bot] | 290870 | 82 | 70 | 180 |

### Failures

- 3x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 36x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
