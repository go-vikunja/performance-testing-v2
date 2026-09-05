# Performance tuning log (2026-09-05)

Goal: find bottlenecks, improve measurably. Hosting/config knobs first, code second.
Infra: ccx23 db + ccx23 vikunja (4 dedicated cores / 16 GB each), postgres:18, vikunja unstable.
Seed: `./reset.sh --users 100 --tasks 80` (100 users x 6 projects x 80 tasks).
Benchmark: `./run-test.sh NAME -u 3000 -r 25 -t 10m` (classes Worker Glancer IntegrationBot), same shape as the
2026-08-30 report. 3000 users is where both boxes are >50 % busy. Throughput is demand-limited (users think), so
the columns to compare are latency, DB/Vikunja CPU and DB ms per request, not rps.

## Results

All runs 3000 users, spawn 25/s, 10 min. "steady" = second half of the full-load window; "ramp" = spawn phase.
CPU and load1 are host averages over the steady window; DB ms per request = `pg_stat_statements` totals / requests.
Runs before the double line have the cost-11 bcrypt ramp and the old locust (bots with JWT, glancers logging in per
session); they are not comparable on ramp numbers or Vikunja CPU with the runs after it.

| run | vikunja | change | rps steady | p50/p95/p99 steady ms | p50/p95 ramp ms | failures | stmts/req | DB exec ms/req | DB plan ms/req | DB CPU % | DB load1 | Vikunja CPU % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-30 report (3000) | v2.5.0-345 | — | ~550 | 140 / 1,500 / 2,000 | 6,000–9,800 / 27,000–45,000 | 345 | 12.6 | 2.4 | n/a | 62 | 21 | 58 |
| `baseline/2026-09-05_22-38-32` | v2.6.0-113 | pool 100, bcrypt 11 | 621 | 19 / 120 / 230 | 4,100 / 16,000 | 88 | 12.9 | 1.34 | 2.32 | 73 | 14.6 | 59 |
| `pool32/2026-09-05_22-53-25` | v2.6.0-119 | pool 32 | 625 | 19 / 70 / 140 | 3,500 / 15,000 | 116 | 12.9 | 0.91 | 1.87 | 72 | 8.1 | 63 |
| `baseline-b4/2026-09-05_23-10-39` | v2.6.0-119 | + bcrypt 4, snapshot restore | 625 | 17 / 42 / 89 | 20 / 62 | 0 | 13.0 | 0.70 | 1.79 | 72 | 5.9 | 51 |
| `pg-nojit/2026-09-05_23-24-47` | v2.6.0-119 | + jit off, no parallel workers | 630 | 17 / 40 / 75 | 20 / 59 | 1 | 13.0 | 0.69 | 1.71 | 71 | 6.1 | 51 |
| ═══ | | new locust: bots with API tokens, glancers refresh | | | | | | | | | | |
| `baseline-v3/2026-09-05_23-41-00` | v2.6.0-119 | pool 32, bcrypt 4, jit off | 605 | 73 / 180 / 260 | 27 / 100 | 4 | 18.5 | 0.93 | 2.39 | 82 | 14.4 | 82 |
| `gogc400/2026-09-06_00-02-58` | v2.6.0-121 | + GOGC 400, GOMEMLIMIT 4GiB | 611 | 62 / 170 / 240 | 27 / 90 | 1 | 18.5 | 0.93 | 2.36 | 82 | 13.9 | 80 |
| `token-cache/2026-09-06_00-17-31` | pr-3774 (= main@pgx + cache) | + pgx driver (#3721) + verified-token cache (#3774) | 634 | **13 / 25 / 110** | 17 / 53 | 1 | 18.7 | 0.67 | **0.82** | **48** | 3.1 | **53** |
| `pg-generic-plan/2026-09-06_00-31-54` | pr-3774 | + plan_cache_mode force_generic_plan (reverted) | 628 | 13 / 23 / 100 | 16 / 50 | 0 | 18.8 | 0.66 | 0.60 | 45 | 3.8 | 53 |
| `conn-lifetime/2026-09-06_00-45-48` | pr-3774 | + connection lifetime 10 s → 1 h | 629 | 13 / 20 / **26** | 16 / 41 | 0 | 18.8 | 0.62 | 0.50 | 44 | 2.0 | 52 |

## State of the recommendations from runs/report-2026-08-30-capacity.md

| rec | status |
|---|---|
| code 1: stop holding a transaction per request | open (`db.NewSession()` still `Begin()`s) |
| code 2a: `parent_project_id` NULL for roots | done (`fc78cd3ea`) |
| code 3: `(project_id, done, due_date)` index | done (`98235c670`) |
| code 4: pgx driver | merged 2026-09-05 (go-vikunja/vikunja#3721, `a5beb8d8`); measured via the pr-3774 image, unstable build stuck in GitHub's runner queue |
| code 7: bcrypt semaphore / login storm | dropped: the 25 logins/s ramp is a test artefact (see below) |
| hosting 1: lower pool | applied (32), kept |
| hosting 3: `jit = off` | applied, kept (within noise, p99 89 → 75) |
| hosting 4: loadgen port range | applied before the first run |

## Log

### 0. Prep

- Loadgen: `ip_local_port_range = 1024 65535`, `tcp_tw_reuse = 1` (`infra/hosts/loadgen/post-deploy.sh`).
  Removes the `OSError(99)` noise that was 249 of 345 failures last time; test-side only.
- Infra bugs found on the way (all fixed + committed): Vikunja healthcheck used `wget` (not in image);
  Prometheus had `http://:9646` for locust and no loadgen node-exporter because the first `setup.sh` rendered
  `prometheus.yml` with an empty `LOADGEN_PIP` and later re-runs never recreated the container (`up -d` does not
  restart on mounted-file changes; now `--force-recreate`). `.env` cleanup missed `*_PIP` lines. New `redeploy.sh`
  to re-apply one host's config / swap the Vikunja image without `setup.sh`. Editing `run-test.sh` while a run was
  in progress corrupted it (bash reads scripts incrementally): the archive step is now `collect-run.sh`, rerunnable.
  `run.sh` kills locust if it has not exited 90 s after the run.
- Every run now starts from the seeded state: `reset.sh` snapshots the seeded db as template `vikunja_snap`,
  `run-test.sh` does `drop database vikunja with (force); create database vikunja template vikunja_snap` first.
  Before this, runs drifted ~4 % per run (task/project creates).
- The first baseline has no locust series in Grafana and a ~2 min Prometheus gap at the end (restart during the
  run). Locust csv + pg_stat_statements are complete.

### 1. Baseline — `runs/baseline/2026-09-05_22-38-32`

- Steady state is fine now (the NULL-parent + composite index commits did their job). The remaining problem is the
  login ramp: p50 4 s, 60 s client timeouts, 14 users died. And the DB box is the wall at 73 % with
  **planning time 2× execution time** (1,370 vs 670 ms/s). Every statement is planned from scratch (lib/pq, unnamed
  prepared statements) — this is exactly what PR #3721 (pgx) addresses.
- Top statements: grants CTE 29 % (0.41 ms exec + 0.55 ms plan, 0.77×/request), home overview `tasks ... project_id
  IN (...) ORDER BY due_date` 20 % in many variants at 14–25 ms mean (still the heavy query for team users),
  `project_hierarchy` per task read 5 % with 1.32 ms *planning* per 0.15 ms exec.
- New Vikunja bug: `pq: duplicate key value violates unique constraint "UQE_tasks_tasks_project_index"` on
  `POST /projects/{id}/tasks` — two concurrent creates in one project compute the same `index`. 1× in 1,734 creates.
  Fixed by go-vikunja/vikunja#3697.

### 2. Pool 100 → 32 — `runs/pool32/2026-09-05_22-53-25` (kept)

`VIKUNJA_DATABASE_MAXOPENCONNECTIONS: 32`. Vikunja image drifted to `v2.6.0-119-g2c22cfb6` on redeploy
(`--pull always`); the 6 commits in between are frontend/editor only. Same throughput, tail latency halved,
DB queueing (load1) almost halved: 100 connections on 4 cores were context-switching against each other.
Statement rate identical, so the CPU saved went into planning, which is still 2× execution.

### Test-side decision: bcrypt cost 4 for all further runs

The ramp (25 logins/s, 3000 users) was a bcrypt-cost-11 CPU benchmark: ~2.5 of 4 cores hashing for the whole
spawn phase, every other request queued behind it, connections idle-in-transaction while hashing. Per the user:
not something to optimise in Vikunja. The test deployment sets `VIKUNJA_SERVICE_BCRYPTROUNDS=4` and the seed was
redone (all hashes cost 4). Glancers also logged in on every session (5–6 logins/s in steady state, ~0.4 cores),
which explains the 59 → 51 % Vikunja CPU drop between baseline and baseline-b4.

### 3. Baseline with bcrypt 4 — `runs/baseline-b4/2026-09-05_23-10-39`

Pool 32, bcrypt 4, fresh seed + snapshot restore. 360,014 requests, 0 failures, all 3000 users alive, ramp
indistinguishable from steady state. DB still at 72 % with **72 % of its statement time in planning**.

### Test-side change: bots use API tokens, glancers refresh

No class used API tokens; real bots do (65 % of production requests). Vikunja verifies an API token with
PBKDF2-SHA256 × 10,000 on every request (`pkg/models/api_tokens.go:142`), a cost the test hid entirely. `seed.py`
now creates one token per account (all `tasks`/`projects`/`labels` permissions from `/routes`), `IntegrationBot`
sends it as bearer and never logs in. `Glancer` refreshes its JWT (10 % fresh login) instead of logging in per
session, matching the access logs (refresh 10 % of interactive requests, login not in the top list).
Requires a reseed; runs after the double line in the table use it.

### 4. `jit = off`, `max_parallel_workers_per_gather = 0` — `runs/pg-nojit/2026-09-05_23-24-47` (kept)

Within run-to-run noise: plan 1.79 → 1.71 ms/req, p99 89 → 75 ms, DB CPU 72 → 71 %. No statement here is expensive
enough to trigger JIT or a parallel plan, so all the setting removes is the planner considering them. Kept because it
cannot hurt an OLTP box; not a lever. Note: the conf change was committed together with the docs commit `e3b221f`
by accident (`git commit -a`).

### 5. Baseline with the new locust — `runs/baseline-v3/2026-09-05_23-41-00`

Same deployment as pg-nojit, only the load changed (bots send `tk_…` API tokens, glancers refresh). Everything got
worse, and that is the finding:

| | pg-nojit (bots with JWT) | baseline-v3 (bots with API token) |
|---|---|---|
| bot `GET /tasks/{id}` p50 / p95 ms | ~20 / ~45 | **92 / 240** |
| steady p50 / p95 / p99 ms | 17 / 40 / 75 | 73 / 180 / 260 |
| Vikunja host CPU / container cores | 51 % / 1.8 | **82 % / 3.2** |
| DB host CPU / load1 | 71 % / 6 | 82 % / 14 |
| statements per request | 13.0 | 18.5 |
| `BEGIN` per request | ~2 | **2.7** |
| `users` by id per request | 1.4 | 2.75 |

Per bot request the API-token path costs, on top of the handler itself:

- **PBKDF2-SHA256 × 10,000 over the raw token** (`models.HashToken`, `pkg/models/api_tokens.go:142`) on every
  request: 3.2 ms single-core measured (Ryzen 4300G; the ccx23 EPYC is similar). At ~320 bot requests/s that is
  1–1.5 cores of the 4, which is the 51 → 82 % jump. There is no cache of verified tokens.
- Its own transaction (`auth.ValidateAPITokenString` → `db.NewSession()`): `BEGIN`, `select … from api_tokens where
  token_last_eight = $1`, `select … from users where id = $1`, `COMMIT` = 4 statements before the handler starts.
  The handler then loads the same user again. Bot requests went from ~10 to ~19 statements.

65 % of Vikunja Cloud's requests are bot requests with API tokens, so in production this is probably the single
largest CPU consumer and the previous reports never saw it. Fix: memoize verified tokens in-process
(digest of the raw token → token id, short TTL), reload the row by primary key so deletion and expiry still apply,
compare the stored hash to catch id reuse. Draft PR: go-vikunja/vikunja#3774.

### 6. `GOGC=400`, `GOMEMLIMIT=4GiB` — `runs/gogc400/2026-09-06_00-02-58` (kept, minor)

2.3 GCs/s at GOGC 100 under the v3 load. With 400: Vikunja container 3.18 → 3.10 cores, p50 73 → 62 ms, RSS 368 →
765 MB. A few percent of CPU for 400 MB of RAM; kept as deployment config, not a lever. Image drifted to
`v2.6.0-121-g700bcd79` (2 commits, no backend perf change).

### 7. pgx + verified-token cache — `runs/token-cache/2026-09-06_00-17-31`

Image `ghcr.io/go-vikunja/vikunja:pr-3774` (revision `11120a71d`; the version string it reports is wrong, the
preview build describes the base). The branch is based on main *after* the pgx merge, so this run has both
changes; CI for main itself has been stuck in GitHub's `ubuntu-latest` queue since 21:29, no unstable build yet.
Attribution by where the time went:

| | gogc400 (lib/pq, PBKDF2 per request) | token-cache (pgx + cache) | lever |
|---|---|---|---|
| DB plan ms per request | 2.36 | 0.82 | pgx (DB-side only) |
| DB exec ms per request | 0.93 | 0.67 | pgx (less contention) |
| DB host CPU / load1 | 82 % / 13.9 | 48 % / 3.1 | pgx |
| Vikunja container cores | 3.10 | 1.87 | token cache (PBKDF2 gone), some pgx |
| bot `GET /tasks/{id}` p50 / p95 ms | 80 / 210 | 14 / 40 | both |
| `GET /tasks [home]` p50 / p95 ms | 61 / 110 | 18 / 54 | pgx |
| steady p50 / p95 / p99 ms | 62 / 170 / 240 | 13 / 25 / 110 | both |

Both boxes are now at ~50 % at 3000 users, where before this session they were at 60–80 % with a much easier
load (JWT bots). Planning is not gone though: 490 ms/s of planning for 400 ms/s of execution. The grants CTE
plans at **0.90 ms per call for 0.36 ms of execution** (280k calls), and even PK lookups show 0.23 ms plan per
call. With prepared statements that means Postgres is still building custom plans on every execution
(`plan_cache_mode = auto` never switches to the generic plan when the generic estimate looks worse). Next:
`plan_cache_mode = force_generic_plan`.

### Finding: the pool recycles every connection every 10 seconds

`database.maxconnectionlifetime` defaults to `10000` (`pkg/config/config.go:422`) and is parsed as milliseconds
(`pkg/db/db.go:173`), so `SetConnMaxLifetime(10s)`. Verified live during a run: every one of the 32 backends in
`pg_stat_activity` is between 0 and 9.3 s old. Consequences:

- pgx's per-connection statement cache and Postgres's per-backend plan cache are thrown away every 10 s. That is why
  planning did not disappear with pgx: 0.23 ms plan per PK lookup and 0.90 ms per grants CTE means nearly every
  execution still gets Parse + plan (`plan_cache_mode = auto` does switch to generic plans after 5 executions,
  checked with `pg_prepared_statements` — the statements just never survive long enough).
- 32 fresh connections every 10 s = ~3 connects/s: auth, `SET search_path`, backend fork on the DB side.
- Sessions that hold a connection longer than the lifetime are not affected (lifetime is checked on return to the
  pool), so nothing breaks; it is purely wasted work.

Fix on the deployment: `VIKUNJA_DATABASE_MAXCONNECTIONLIFETIME=3600000` (1 h). Fix in Vikunja: change the default
(the value is documented in seconds in older docs, which is probably where the 10000 came from).

### 8. `plan_cache_mode = force_generic_plan` — `runs/pg-generic-plan/2026-09-06_00-31-54` (reverted)

Planning 0.82 → 0.60 ms/req, DB CPU 48 → 45 %, but the grants CTE's plan cost per call went 0.90 → 2.39 ms: a generic
plan for a recursive CTE is expensive to build and it is still rebuilt every 10 s (see the lifetime finding). Not the
right lever, and generic plans for the `project_id IN (...)` family are a risk on skewed data. Reverted to `auto`.

### 9. Connection lifetime 10 s → 1 h — `runs/conn-lifetime/2026-09-06_00-45-48` (kept)

`VIKUNJA_DATABASE_MAXCONNECTIONLIFETIME=3600000`. p99 110 → 26 ms (the reconnect every 10 s was the tail),
planning 0.82 → 0.50 ms/req, DB load1 3.1 → 2.0. PR for the default: go-vikunja/vikunja#3775.
Planning is still not near zero though: 0.22 ms per PK lookup, 0.53 ms per grants CTE, on nearly every call. So
statements are still being re-prepared. Remaining suspect: pgx's per-connection statement cache holds 512 entries
and Vikunja generates many distinct SQL texts (`IN ($1, …, $N)` with per-user N, per-view variants), so the LRU
churns. Probing with `log_statement = all`.
