# Findings: unstable-pgx / 2026-09-06_01-08-54

```
run=2026-09-06_01-08-54 name=unstable-pgx users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788649711000 to=1788650402000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788649711000&to=1788650402000
vikunja_version=v2.6.0-141-g8ba3bbdf
```

## Locust summary

- requests: 356755  failures: 0  rps: 576.7308516461618
- response time ms: p50 21  p95 61  p99 110  max 1131.76988899977
- postgres: 6686024 statements = 18.7 per request, 0.72 ms DB exec + 0.53 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 400 | 58 | 49 | 130 |
| POST /login | 2950 | 49 | 46 | 82 |
| GET /tasks [bot] | 6034 | 38 | 31 | 76 |
| PATCH /tasks/{id} [patch] | 2467 | 34 | 26 | 77 |
| GET /tasks/{id} [bot] | 132873 | 33 | 26 | 72 |
| POST /projects/{id}/tasks [create] | 2049 | 32 | 26 | 67 |
| GET /projects [bot] | 18346 | 31 | 25 | 68 |
| GET /projects/{id}/tasks [bot] | 46957 | 31 | 25 | 67 |
| GET /tasks [home] | 11017 | 30 | 25 | 63 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3945 | 29 | 24 | 63 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
