# Findings: pool32 / 2026-09-05_22-53-25

```
run=2026-09-05_22-53-25 name=pool32 users=3000 spawn_rate=25 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788641575000 to=1788642267000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788641575000&to=1788642267000
vikunja_version=v2.6.0-119-g2c22cfb6
```

## Locust summary

- requests: 304667  failures: 116  rps: 495.6893402849475
- response time ms: p50 20  p95 3000  p99 20000  max 60035.23729899985
- postgres: 3938428 statements = 12.9 per request, 0.91 ms DB exec + 1.87 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 6267 | 11719 | 5900 | 43000 |
| GET /user | 4499 | 4363 | 580 | 21000 |
| GET /projects | 4499 | 4224 | 730 | 20000 |
| GET /labels | 4499 | 3529 | 490 | 17000 |
| GET /tasks [home] | 9560 | 1936 | 40 | 11000 |
| PATCH /tasks/{id} [patch] | 1924 | 889 | 38 | 3300 |
| POST /projects/{id}/tasks [create] | 1661 | 694 | 38 | 2400 |
| POST /tasks/{id}/labels [add] | 651 | 670 | 25 | 2900 |
| POST /projects [create] | 362 | 640 | 63 | 2500 |
| GET /projects/{id}/views/{view}/tasks [list] | 12485 | 628 | 28 | 2700 |

### Failures

- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf48', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf30', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/42067', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf77', 0, original=timed out)
- 4x GET /user: RetriesExceeded('http://10.0.1.2:3456/api/v2/user', 0, original=timed out)
- 1x PATCH /tasks/{id} [patch]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/33668', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/220', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf96', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/15820', 0, original=timed out)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/338/tasks', 0, original=timed out)
- 2x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf27', 0, original=timed out)
- 1x GET /tasks/{id}/comments: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/9010/comments', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/15858', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/547', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/503', 0, original=timed out)
- 1x PATCH /tasks/{id} [patch]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/12987', 0, original=timed out)
- 1x POST /tasks/{id}/labels [add]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/13775/labels', 0, original=timed out)
- 2x GET /tasks [home]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/5715', 0, original=timed out)
- 1x GET /tasks/{id} [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/tasks/6047', 0, original=timed out)
- 3x GET /labels: RetriesExceeded('http://10.0.1.2:3456/api/v2/labels', 0, original=timed out)
- 1x GET /avatar/{username}: RetriesExceeded('http://10.0.1.2:3456/api/v2/avatar/perf87', 0, original=timed out)
- 75x POST /login: RetriesExceeded('http://10.0.1.2:3456/api/v2/login', 0, original=timed out)
- 1x GET /projects/{id}: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/512', 0, original=timed out)
- 10x GET /projects: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects', 0, original=timed out)
- 1x GET /projects/{id}/tasks [bot]: RetriesExceeded('http://10.0.1.2:3456/api/v2/projects/326/tasks', 0, original=timed out)
- 20x exception: the JSON object must be str, bytes or bytearray, not NoneType

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
