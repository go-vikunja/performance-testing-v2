# Findings: baseline / 2026-09-05_22-38-32

```
run=2026-09-05_22-38-32 name=baseline users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788640686000 to=1788641377000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788640686000&to=1788641377000
vikunja_version=v2.6.0-113-g7d1aee8d
```

## Locust summary

- requests: 304579  failures: 88  rps: 498.7018770596425
- response time ms: p50 20  p95 3100  p99 20000  max 60039.702314999886
- postgres: 3916633 statements = 12.9 per request, 1.34 ms DB exec + 2.32 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 6277 | 11294 | 5900 | 41000 |
| GET /projects | 4526 | 4151 | 1100 | 20000 |
| GET /user | 4526 | 4099 | 630 | 20000 |
| GET /labels | 4526 | 3630 | 600 | 17000 |
| GET /tasks [home] | 9560 | 2077 | 46 | 12000 |
| PATCH /tasks/{id} [patch] | 2018 | 981 | 41 | 4900 |
| POST /projects [create] | 378 | 929 | 63 | 6200 |
| POST /projects/{id}/tasks [create] | 1734 | 732 | 39 | 3700 |
| GET /projects/{id}/views/{view}/tasks [list] | 12724 | 668 | 29 | 3000 |
| PUT /tasks/{id}/position | 1044 | 604 | 20 | 2900 |

### Failures

- 1x GET /tasks/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/11642', 0, original=timed out)
- 5x GET /user: RetriesExceeded('http://10.0.1.2:3456/api/v2/user', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/18178', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf78', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/26498', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf57', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/255', 0, original=timed out)
- 1x GET /projects [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/503', 0, original=timed out)
- 1x GET /tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks', 0, original=timed out)
- 4x GET /tasks [home]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks', 0, original=timed out)
- 1x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)
- 2x GET /labels: RetriesExceeded('http://10.0.1.2:3456/api/v2/labels', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf87', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/19427', 0, original=timed out)
- 59x POST /login: RetriesExceeded('http://10.0.1.2:3456/api/v2/login', 0, original=timed out)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/494/tasks', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/41421', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf47', 0, original=timed out)
- 2x GET /projects: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/2077', 0, original=timed out)
- 14x exception: the JSON object must be str, bytes or bytearray, not NoneType

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
