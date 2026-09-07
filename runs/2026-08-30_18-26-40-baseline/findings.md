# Findings: baseline / 2026-08-30_18-26-40

```
run=2026-08-30_18-26-40 name=baseline users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788107177000 to=1788107868000
grafana_url=http://178.104.207.216:3000/d/perf-overview/perf-overview?from=1788107177000&to=1788107868000
vikunja_version=v2.5.0-345-g5694ef63
```

## Locust summary

- requests: 271067  failures: 345  rps: 438.8246366029645
- response time ms: p50 140  p95 5100  p99 22000  max 60106.8771539999
- postgres: 3417853 statements = 12.6 per request, 2.41 ms DB exec time per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 6281 | 11878 | 6400 | 43000 |
| GET /projects | 4506 | 4608 | 1600 | 21000 |
| GET /user | 4506 | 4310 | 1000 | 19000 |
| GET /labels | 4506 | 4087 | 1500 | 18000 |
| GET /tasks [home] | 9318 | 2487 | 280 | 12000 |
| PATCH /tasks/{id} [patch] | 1840 | 1520 | 160 | 7500 |
| POST /projects [create] | 291 | 1310 | 200 | 6700 |
| GET /projects/{id}/views/{view}/tasks [list] | 11702 | 1228 | 190 | 5700 |
| POST /projects/{id}/tasks [create] | 1575 | 1076 | 150 | 5100 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 3124 | 1060 | 240 | 4200 |

### Failures

- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf24', 0, original=timed out)
- 39x GET /projects/{id}/tasks [bot]: OSError(99, 'Cannot assign requested address')
- 2x GET /projects/{id}/views/{view}/buckets/tasks [kanban]: OSError(99, 'Cannot assign requested address')
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/1747', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf91', 0, original=timed out)
- 15x POST /user/token/refresh: OSError(99, 'Cannot assign requested address')
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/321', 0, original=timed out)
- 127x GET /tasks/{id} [bot]: OSError(99, 'Cannot assign requested address')
- 1x GET /projects/{id}/views/{view}/tasks [list]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/698/views/3189/tasks', 0, original=timed out)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/332/tasks', 0, original=timed out)
- 1x PUT /tasks/{id}/read: OSError(99, 'Cannot assign requested address')
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/24378', 0, original=timed out)
- 6x GET /tasks [home]: OSError(99, 'Cannot assign requested address')
- 3x GET /user: RetriesExceeded('http://10.0.1.2:3456/api/v2/user', 0, original=timed out)
- 5x PATCH /tasks/{id} [patch]: OSError(99, 'Cannot assign requested address')
- 1x GET /labels: OSError(99, 'Cannot assign requested address')
- 1x PATCH /tasks/{id} [patch]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/34527', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf39', 0, original=timed out)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/362/tasks', 0, original=timed out)
- 2x GET /projects [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf80', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/395', 0, original=timed out)
- 2x POST /login: OSError(99, 'Cannot assign requested address')
- 6x GET /projects/{id}/views/{view}/tasks [list]: OSError(99, 'Cannot assign requested address')
- 1x GET /projects/{id}/views/{view}/tasks [gantt]: OSError(99, 'Cannot assign requested address')
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/25786', 0, original=timed out)
- 5x GET /tasks [home]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks', 0, original=timed out)
- 12x GET /projects/{id}: OSError(99, 'Cannot assign requested address')
- 5x GET /tasks/{id}: OSError(99, 'Cannot assign requested address')
- 1x PUT /tasks/{id}/position: OSError(99, 'Cannot assign requested address')
- 3x GET /tasks/{id}/comments: OSError(99, 'Cannot assign requested address')
- 3x GET /labels: RetriesExceeded('http://10.0.1.2:3456/api/v2/labels', 0, original=timed out)
- 59x POST /login: RetriesExceeded('http://10.0.1.2:3456/api/v2/login', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf26', 0, original=timed out)
- 1x GET /tasks [bot]: OSError(99, 'Cannot assign requested address')
- 11x GET /avatar/{username}: OSError(99, 'Cannot assign requested address')
- 4x GET /projects: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/18128', 0, original=timed out)
- 15x GET /projects [bot]: OSError(99, 'Cannot assign requested address')
- 1x GET /info: OSError(99, 'Cannot assign requested address')
- 17x exception: the JSON object must be str, bytes or bytearray, not NoneType

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- Steady state: ~550 rps, p50 140 / p95 1.5 s / p99 2.0 s (yesterday 200 / 1.9 s / 2.5 s at 510 rps). DB exec per request 5.6 → 2.4 ms, Postgres 3.0 → 2.4 cores, load1 49 → 32.
- Ramp (0–140 s): rps stuck at ~125, p50 up to 9.8 s, 64–84 backends idle in transaction = the 100-connection pool full of logins waiting on bcrypt.
- All 345 failures are loadgen-side: 249× `OSError 99` (ephemeral ports exhausted, TIME_WAIT peaked at 24k), ~80 client timeouts during the ramp, 17 locust exceptions. Zero HTTP 5xx; Vikunja log has no errors besides 22k `user in context is not jwt token` lines from the metrics middleware.
- Top statement: grants CTE 48 % of DB time; its recursive step full-scans `IDX_projects_parent_project_id` because root projects store `parent_project_id = 0`. Home overview query 29 ms mean: planner uses the new `(done, due_date)` index and filters 3.7k rows for users with ~30 projects.
- See `runs/report-2026-08-30-capacity.md`.
