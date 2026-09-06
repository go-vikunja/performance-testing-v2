# Findings: pool400-cap20000 / 2026-09-06_16-52-02

```
run=2026-09-06_16-52-02 name=pool400-cap20000 users=20000 spawn_rate=125 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788706299000 to=1788706991000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788706299000&to=1788706991000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 2295493  failures: 36  rps: 3708.1330578656994
- response time ms: p50 30  p95 82  p99 130  max 1174.5679690002362
- postgres: 30131806 statements = 13.1 per request, 0.43 ms DB exec + 0.17 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 2478 | 119 | 110 | 230 |
| POST /projects/{id}/tasks [create] | 12909 | 67 | 61 | 130 |
| PATCH /tasks/{id} [patch] | 15488 | 62 | 52 | 150 |
| GET /tasks [home] | 70407 | 61 | 55 | 130 |
| GET /tasks [bot] | 38822 | 60 | 55 | 120 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 26029 | 55 | 50 | 110 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 5114 | 51 | 45 | 110 |
| GET /projects | 32105 | 51 | 44 | 100 |
| GET /tasks/{id} | 30743 | 48 | 44 | 98 |
| GET /projects [bot] | 117424 | 46 | 43 | 94 |

### Failures

- 1x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 35x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
