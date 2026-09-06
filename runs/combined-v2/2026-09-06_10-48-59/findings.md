# Findings: combined-v2 / 2026-09-06_10-48-59

```
run=2026-09-06_10-48-59 name=combined-v2 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788684517000 to=1788685208000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788684517000&to=1788685208000
vikunja_version=v2.6.0-146-gd22c895b
```

## Locust summary

- requests: 363260  failures: 0  rps: 587.1171146931373
- response time ms: p50 11  p95 22  p99 39  max 1044.2606549986522
- postgres: 6557002 statements = 18.1 per request, 0.48 ms DB exec + 0.15 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 2932 | 35 | 35 | 55 |
| POST /projects [create] | 405 | 28 | 26 | 42 |
| GET /projects | 4923 | 18 | 17 | 37 |
| GET /tasks [bot] | 6258 | 18 | 17 | 25 |
| GET /tasks [home] | 10889 | 18 | 15 | 31 |
| POST /projects/{id}/tasks [create] | 2067 | 17 | 16 | 25 |
| PATCH /tasks/{id} [patch] | 2432 | 17 | 16 | 31 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4049 | 16 | 15 | 25 |
| GET /projects/{id}/views/{view}/tasks [gantt] | 821 | 15 | 14 | 23 |
| GET /projects [bot] | 18742 | 14 | 13 | 19 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
