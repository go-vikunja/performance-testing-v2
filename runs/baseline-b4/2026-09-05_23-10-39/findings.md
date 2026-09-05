# Findings: baseline-b4 / 2026-09-05_23-10-39

```
run=2026-09-05_23-10-39 name=baseline-b4 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788642616000 to=1788643307000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788642616000&to=1788643307000
vikunja_version=v2.6.0-119-g2c22cfb6
```

## Locust summary

- requests: 360014  failures: 0  rps: 584.4863758280062
- response time ms: p50 18  p95 52  p99 100  max 1026.3011530000767
- postgres: 4684815 statements = 13.0 per request, 0.70 ms DB exec + 1.79 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /projects [create] | 396 | 69 | 57 | 150 |
| PATCH /tasks/{id} [patch] | 2334 | 43 | 35 | 100 |
| POST /projects/{id}/tasks [create] | 1954 | 42 | 34 | 90 |
| GET /tasks [home] | 10730 | 38 | 30 | 83 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 4052 | 37 | 31 | 78 |
| POST /login | 6577 | 34 | 32 | 81 |
| GET /tasks/{id} | 4870 | 34 | 27 | 73 |
| GET /projects | 4862 | 33 | 29 | 71 |
| GET /projects/{id}/views/{view}/tasks [list] | 14558 | 30 | 25 | 63 |
| GET /tasks [bot] | 6169 | 30 | 25 | 63 |

### Failures

none

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
