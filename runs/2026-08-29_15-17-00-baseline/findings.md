# Findings: baseline / 2026-08-29_15-17-00

```
run=2026-08-29_15-17-00 name=baseline users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788009394000 to=1788011137000
grafana_url=http://178.104.196.14:3000/d/perf-overview/perf-overview?from=1788009394000&to=1788011137000
vikunja_version=v2.5.0-249-gc0ebf473
```

## Locust summary

- requests: 266472  failures: 9  rps: 162.17773721924087
- response time ms: p50 220  p95 4300  p99 16000  max 60042.68491200037
- postgres: 3914864 statements = 14.7 per request, 5.56 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 6361 | 7710 | 3800 | 27000 |
| GET /projects | 4636 | 3383 | 1600 | 14000 |
| GET /labels | 4633 | 3286 | 1900 | 12000 |
| GET /user | 4638 | 2928 | 780 | 13000 |
| GET /tasks [home] | 9458 | 2230 | 630 | 9700 |
| POST /projects [create] | 360 | 1430 | 380 | 6500 |
| GET /projects/{id}/views/{view}/tasks [list] | 12081 | 1366 | 430 | 4500 |
| PATCH /tasks/{id} [patch] | 1893 | 1317 | 260 | 6500 |
| GET /tasks/{id}/comments | 3952 | 1246 | 380 | 4000 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3214 | 1228 | 480 | 3700 |

### Failures

- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/25488', 0, original=timed out)
- 1x GET /tasks [home]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks', 0, original=timed out)
- 3x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/472/tasks', 0, original=timed out)
- 3x POST /login: RetriesExceeded('http://10.0.1.2:3456/api/v2/login', 0, original=timed out)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
