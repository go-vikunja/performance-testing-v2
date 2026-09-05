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
