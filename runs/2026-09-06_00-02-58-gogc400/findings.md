# Findings: gogc400 / 2026-09-06_00-02-58

```
run=2026-09-06_00-02-58 name=gogc400 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788645757000 to=1788646448000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788645757000&to=1788646448000
vikunja_version=v2.6.0-121-g700bcd79
```

## Locust summary

- requests: 348646  failures: 1  rps: 563.8221618220157
- response time ms: p50 57  p95 170  p99 290  max 1010.287289000189
- postgres: 6446944 statements = 18.5 per request, 0.93 ms DB exec + 2.36 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 410 | 139 | 140 | 200 |
| GET /tasks [bot] | 5833 | 104 | 90 | 220 |
| GET /tasks/{id} [bot] | 126577 | 94 | 80 | 210 |
| PATCH /tasks/{id} [patch] | 2322 | 93 | 84 | 190 |
| GET /projects/{id}/tasks [bot] | 44496 | 92 | 77 | 210 |
| GET /projects [bot] | 17503 | 88 | 73 | 200 |
| POST /projects/{id}/tasks [create] | 2003 | 85 | 84 | 140 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4059 | 74 | 72 | 120 |
| GET /tasks/{id} | 4813 | 69 | 66 | 120 |
| GET /tasks [home] | 10923 | 66 | 61 | 110 |

### Failures

- 1x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
