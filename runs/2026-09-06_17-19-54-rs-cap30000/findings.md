# Findings: rs-cap30000 / 2026-09-06_17-19-54

```
run=2026-09-06_17-19-54 name=rs-cap30000 users=30000 spawn_rate=187 duration=10m classes="Worker Glancer IntegrationBot" env="LOCUST_PROCESSES=16"
vikunja_image=ghcr.io/go-vikunja/vikunja:pr-3779 postgres_image=postgres:18 types=ccx33/ccx23
from=1788707971000 to=1788708663000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788707971000&to=1788708663000
vikunja_version=v2.6.0-163-gf1c764e7
```

## Locust summary

- requests: 2927658  failures: 171  rps: 4711.316945672841
- response time ms: p50 280  p95 820  p99 2500  max 17955.58585299932
- postgres: 30115661 statements = 10.3 per request, 0.58 ms DB exec + 0.22 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 36128 | 578 | 470 | 1600 |
| GET /projects/{id}/views/{view}/tasks [list] | 135449 | 520 | 410 | 1500 |
| GET /tasks [home] | 102297 | 476 | 380 | 1200 |
| POST /projects [create] | 3623 | 453 | 420 | 760 |
| GET /tasks/{id} | 43877 | 448 | 410 | 820 |
| GET /tasks [bot] | 44969 | 445 | 420 | 800 |
| PATCH /tasks/{id} [patch] | 21580 | 426 | 380 | 780 |
| GET /projects | 47768 | 419 | 250 | 1700 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 7264 | 396 | 350 | 720 |
| POST /login | 29202 | 381 | 70 | 1800 |

### Failures

- 28x POST /user/token/refresh: LocustBadStatusCode(code=401)
- 143x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
