# Performance tuning log (2026-09-05)

Goal: find bottlenecks, improve measurably. Hosting/config knobs first, code second.
Infra: ccx23 db + ccx23 vikunja (4 dedicated cores / 16 GB each), postgres:18, vikunja `v2.6.0-113-g7d1aee8d`.
Seed: `./reset.sh --users 100 --tasks 80` (100 users x 6 projects x 80 tasks).
Benchmark: `./run-test.sh NAME -u 3000 -r 25 -t 10m` (classes Worker Glancer IntegrationBot), same as the
2026-08-30 report so numbers are comparable. 3000 users is where both boxes hit >60 % and the pool piles up;
500/1500 were never bound by anything.

## State of the recommendations from runs/report-2026-08-30-capacity.md

| rec | status |
|---|---|
| code 1: stop holding a transaction per request | open (`db.NewSession()` still `Begin()`s) |
| code 2a: `parent_project_id` NULL for roots | done (`fc78cd3ea`) |
| code 3: `(project_id, done, due_date)` index | done (`98235c670`) |
| code 4: pgx driver | draft PR go-vikunja/vikunja#3721, image `ghcr.io/go-vikunja/vikunja:pr-3721` |
| hosting 1: lower pool | not applied (still 100) |
| hosting 3: `jit = off` | not applied |
| hosting 4: loadgen port range | applied today before the baseline (see below) |

## Log

### 0. Prep

- Loadgen: `ip_local_port_range = 1024 65535`, `tcp_tw_reuse = 1` (`infra/hosts/loadgen/post-deploy.sh`).
  Applied live before any run. Removes the `OSError(99)` noise that was 249 of 345 failures last time; test-side only.
- Infra bugs found on the way (all fixed + committed): Vikunja healthcheck used `wget` (not in image);
  Prometheus had `http://:9646` for locust and no loadgen node-exporter because the first `setup.sh` rendered
  `prometheus.yml` with an empty `LOADGEN_PIP` and later re-runs never recreated the container (`up -d` does not
  restart on mounted-file changes; now `--force-recreate`). `.env` cleanup missed `*_PIP` lines. New `redeploy.sh`
  to re-apply one host's config / swap the Vikunja image without `setup.sh`.
  Consequence: the baseline run below has no locust series in Grafana and a ~2 min Prometheus gap at the end
  (restart during the run). Locust csv + pg_stat_statements are complete.

### 1. Baseline — `runs/baseline/2026-09-05_22-38-32` (3000 users, 25/s, 10 min, vikunja v2.6.0-113-g7d1aee8d)

| | this run | 2026-08-30 |
|---|---|---|
| requests / failures | 304,579 / 88 (0 port errors, 59 login timeouts, 1× 500) | 271,067 / 345 |
| steady rps / p50 / p95 / p99 ms | 621 / 19 / 120 / 230 | ~550 / 140 / 1,500 / 2,000 |
| ramp p50 / p95 ms | 4,100 / 16,000 | 6,000–9,800 / 27,000–45,000 |
| statements per request | 12.9 | 12.6 |
| DB exec + plan ms per request | 1.34 + **2.32** | 2.4 + n/a (planning not tracked) |
| DB host CPU avg / max (steady) | 73 % / 82 % | 62 % / 73 % |
| Vikunja host CPU avg | 59 % | 58 % |
| pg backends idle-in-tx avg / max | 3.4 / 36 | 9.8 / 94 |

- Steady state is fine now (the NULL-parent + composite index commits did their job). The remaining problem is the
  login ramp: p50 4 s, 60 s client timeouts, 14 users died. And the DB box is the wall at 73 % with
  **planning time 2× execution time** (1,370 vs 670 ms/s). Every statement is planned from scratch (lib/pq, unnamed
  prepared statements) — this is exactly what PR #3721 (pgx) addresses.
- Top statements: grants CTE 29 % (0.41 ms exec + 0.55 ms plan, 0.77×/request), home overview `tasks ... project_id
  IN (...) ORDER BY due_date` 20 % in many variants at 14–25 ms mean (still the heavy query for team users),
  `project_hierarchy` per task read 5 % with 1.32 ms *planning* per 0.15 ms exec.
- New Vikunja bug: `pq: duplicate key value violates unique constraint "UQE_tasks_tasks_project_index"` on
  `POST /projects/{id}/tasks` — two concurrent creates in one project compute the same `index`. 1× in 1,734 creates.
