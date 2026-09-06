# Findings: combined-v5-cap6000 / 2026-09-06_12-28-53

```
run=2026-09-06_12-28-53 name=combined-v5-cap6000 users=6000 spawn_rate=50 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788690503000 to=1788691187000
grafana_url=http://178.104.3.213:3000/d/perf-overview/perf-overview?from=1788690503000&to=1788691187000
vikunja_version=v2.6.0-150-gd9af013b
```

## Locust summary

- requests: 720856  failures: 4  rps: 1167.034851384056
- response time ms: p50 10  p95 39  p99 90  max 1173.891623999225
- postgres: 9493571 statements = 13.2 per request, 0.38 ms DB exec + 0.11 ms planning per request

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 5913 | 71 | 61 | 140 |
| POST /projects [create] | 763 | 33 | 27 | 66 |
| GET /projects | 9866 | 31 | 23 | 100 |
| GET /info | 9866 | 27 | 11 | 110 |
| GET /tasks [home] | 21618 | 26 | 18 | 55 |
| GET /user | 9866 | 25 | 13 | 110 |
| POST /user/token/refresh | 11719 | 25 | 14 | 61 |
| WS connect+auth+subscribe | 9866 | 23 | 17 | 54 |
| POST /projects/{id}/tasks [create] | 3802 | 21 | 16 | 45 |
| PATCH /tasks/{id} [patch] | 4781 | 21 | 15 | 47 |

### Failures

- 4x POST /projects/{id}/tasks [create]: LocustBadStatusCode(code=500)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- 
