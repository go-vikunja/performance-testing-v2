# Findings: baseline / 2026-08-29_14-39-29

```
run=2026-08-29_14-39-29 name=baseline users=500 spawn_rate=10 duration=10m classes="Worker Glancer IntegrationBot" env=""
vikunja_image=vikunja/vikunja:unstable postgres_image=postgres:18 types=ccx23/ccx23
from=1788007142000 to=1788007808000
grafana_url=http://178.104.196.14:3000/d/perf-overview/perf-overview?from=1788007142000&to=1788007808000
vikunja_version=v2.5.0-249-gc0ebf473
```

## Locust summary

- requests: 63974  failures: 4  rps: 106.65799373648233
- response time ms: p50 17  p95 37  p99 320  max 511.8655939995733

### Slowest endpoints (avg ms)

| endpoint | reqs | avg | p50 | p95 |
|---|---|---|---|---|
| POST /login | 1134 | 232 | 160 | 360 |
| POST /projects [create] | 62 | 58 | 51 | 65 |
| GET /projects | 848 | 48 | 24 | 150 |
| GET /labels | 848 | 35 | 33 | 52 |
| PATCH /tasks/{id} [patch] | 444 | 33 | 28 | 53 |
| GET /tasks [bot] | 1088 | 33 | 28 | 38 |
| GET /projects/{id}/views/{view}/buckets/tasks [kanban] | 707 | 33 | 31 | 41 |
| GET /tasks/{id} | 750 | 29 | 25 | 35 |
| GET /tasks [home] | 1927 | 29 | 27 | 38 |
| PUT /projects/{id}/views/{view}/buckets/{bucket}/tasks [move] | 102 | 28 | 24 | 40 |

### Failures

- 4x POST /tasks/{id}/labels [add]: LocustBadStatusCode(code=400)

## Postgres

See `pg-top-statements.txt`, `pg-seq-scans.txt`, `grafana/`.

## Observations

- No bottleneck at 500 users / 107 rps: DB host 28 % CPU, Vikunja host 22 %, Postgres ~150 ms exec time per
  second (0.15 busy backends), Vikunja container ~1 core. Memory flat. Response times stable after the ramp-up
  spike (avg 78 ms while 500 users log in at once, then settling at ~22 ms avg, p50 17 ms, p95 37 ms).
- 954,904 statements for 63,974 requests = **15 queries per API request**, avg 0.1 ms each. DB exec time is
  ~1 ms per request while the request takes ~18 ms (excluding login): time is spent in Vikunja + 15 round-trips,
  not in Postgres. Reducing query count per request is the lever, not query tuning.
- p99 (320 ms) and max are `POST /login` (bcrypt, 232 ms avg). Expected; excluded from the above.
- Top statements by total time: the recursive `project_hierarchy` CTE (41k calls, permission checks for
  single projects), `all_projects` CTE (project list, ~1.5 ms), and the label listing for `/labels`
  (`labels ... task_id IN (SELECT id FROM tasks WHERE project_id IN (<all 700 project ids>))`, 9.5 ms + a
  separate `count(DISTINCT)` of 7.8 ms per call) — `/labels` is 35 ms avg here and 271 ms p50 on Cloud.
- `GET /projects` p95 150 ms vs p50 24 ms: bimodal, the slow mode is the `is_archived=true&expand=permissions`
  app-load variant.
- Seq scans: `projects` 133k seq scans / 103M tuples read, `team_members` 122k seq scans (its user_id index was
  used 6 times), `labels` 31k. Tables are tiny here (700 / 80 / 600 rows) so the planner prefers seq scans;
  worth re-checking in the big-workspace scenario where the same CTEs run over thousands of rows.
- Write share is small (~6k writes vs 426k reads by statement kind), matching the Cloud log (~3 % writes).
- 4× `POST /tasks/{id}/labels` 400: label already on the task (random re-add). Test noise, now tolerated.
