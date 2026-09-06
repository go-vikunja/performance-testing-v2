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
| `unstable-pgx/2026-09-06_01-08-54` | v2.6.0-141 (unstable, pgx, no token cache) | same config, main without #3774 | 626 | 21 / 55 / 84 | 19 / 55 | 1 | 18.7 | 0.72 | 0.53 | 46 | 2.5 | **79** |
| `sub-params/2026-09-06_01-23-01` | pr-3776 (= unstable + #3776, no token cache) | + subscription ids as parameters | 627 | 20 / 49 / 73 | 18 / 50 | 1 | 18.7 | 0.84 | **0.15** | 42 | 2.6 | 78 |
| `cap6000/2026-09-06_01-51-04` (**6000 users**, 50/s) | pr-3774 | capacity run, pgx + token cache | **1242** | 24 / 85 / 130 | 24 / 77 | 3 | 18.6 | 0.96 | 0.70 | 85 | 15.9 | 79 |
| `partial-index/2026-09-06_02-08-51` | pr-3774 | + partial index on projects.parent_project_id (#3777, applied live) | 636 | 13 / 19 / 24 | 16 / 41 | 0 | 18.6 | **0.52** | 0.48 | 42 | 2.0 | 52 |
| `combined/2026-09-06_10-05-12` | pr-3779 (`ea603a21a` = main + #3774 #3775 #3776 #3777 #3780) | all five together | 636 | **11 / 17 / 22** | 15 / 39 | 2 | 18.2 | 0.53 | **0.14** | **37** | 2.3 | 50 |
| `combined-cap6000/2026-09-06_10-18-07` (**6000 users**, 50/s) | pr-3779 (`ea603a21a`) | all five, capacity | **1251** | 14 / 41 / 66 | 23 / 72 | 0 | 18.2 | 0.47 | 0.15 | 56 | 4.0 | 77 |
| `combined-v2/2026-09-06_10-48-59` | pr-3779 (`7a6414d20` = + #3780 keyvalue refactor + #3783) | + hook-less project touch | 633 | 11 / 17 / 22 | 14 / 38 | 0 | 18.1 | **0.48** | 0.15 | 37 | **1.5** | 50 |
| `combined-profile/2026-09-06_11-21-58` | pr-3779 (`f3bb05960` = + #3785 pprof) | same as v2, 30 s CPU profile at t=240 (`cpu-profile-t240-30s.pb.gz` in the run dir) | 627 | 11 / 17 / 23 | 14 / 38 | 0 | 18.0 | 0.49 | 0.15 | 37 | 1.3 | 50 |
| `combined-v3/2026-09-06_11-43-28` | pr-3779 (`b089ac163` = + #3786) | + regexp/logger/auth per-request overhead | 640 | **10 / 16 / 22** | 13 / 37 | 0 | **14.6** | 0.53 | 0.17 | 39 | 1.4 | **45** |
| `combined-v4/2026-09-06_12-01-18` | pr-3779 (`eee403ef8` = + WITH word scan) | + regexp-free write detection | 637 | **9** / 16 / 22 | 13 / 39 | 1 | 14.6 | 0.55 | 0.17 | 39 | 1.9 | **43** |
| `combined-v5/2026-09-06_12-15-02` | pr-3779 (`cb03108cc` = + #3787) | + per-session memo for task/project/user lookups | 638 | 9 / 16 / 22 | 12 / 37 | 0 | **13.2** | 0.55 | 0.18 | 39 | 2.7 | **41** |
| `combined-v5-cap6000/2026-09-06_12-28-53` (**6000 users**, 50/s) | pr-3779 (`cb03108cc`, all PRs) | capacity, final image | **1259** | 9 / 21 / 34 | 22 / 68 | 4 | 13.2 | 0.38 | 0.11 | 43 | 2.3 | 65 |
| `cap9000/2026-09-06_13-57-32` (**9000 users**, 75/s, 4 locust procs) | pr-3779 (`cb03108cc`) | capacity, past the knee | **1873** | 11 / **68 / 130** | 19 / 99 | 6 | 13.2 | 0.45 | 0.14 | 68 | 5.8 | **83** |
| `cap10000/2026-09-06_14-41-42` (**10000 users**, 80/s, **ccx33 + ccx33**) | pr-3779 (`cb03108cc`) | bigger boxes: 8 cores / 32 GB each, pool 48, shared_buffers 8 GB | **2107** | **6 / 10 / 14** | 9 / 59 | 2 | 13.1 | 0.23 | 0.08 | 25 | 2.3 | 60 |
| `cap14000/2026-09-06_15-01-21` (**14000 users**, 100/s, ccx33 + ccx33, cx43 loadgen, 8 locust procs) | pr-3779 | ceiling for p99 < 50 ms | **2947** | 6 / 20 / **45** | 9 / 64 | 8 | 13.1 | 0.27 | 0.09 | 39 | 2.6 | **76** |
| `db23-cap12000/2026-09-06_15-28-58` (**12000 users**, ccx33 API + **ccx23 DB**) | pr-3779 | ceiling with the small DB | **2518** | 9 / 28 / **47** | 19 / 110 | 5 | 13.1 | 0.67 | 0.18 | **87** | 13.0 | 50 |
| `big-cap20000/2026-09-06_16-08-58` (**20000 users**, ccx53 API 32c + ccx43 DB 16c, pool 48) | pr-3779 | pool saturated | 3603 | 200 / 690 / 1000 | 17 / 100 | 22 | 12.8 | 0.45 | 0.13 | 37 | 5.6 | 40 |
| `pool192-cap20000/2026-09-06_16-23-33` (20000 users, big boxes, pool 192, max idle 50) | pr-3779 | connection churn | 4056 | 57 / 130 / 180 | 27 / 140 | 39 | 13.1 | 0.58 | **0.75** | 60 | 19.9 | 41 |
| `idle192-cap20000/2026-09-06_16-37-47` (20000 users, big boxes, pool 192, idle 192) | pr-3779 | pool still bursting full | 4145 | 32 / 71 / 94 | 15 / 68 | 34 | 13.1 | 0.43 | 0.15 | 41 | 6.1 | 41 |

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
load (JWT bots). Planning is not gone though: 490 ms/s of planning for 400 ms/s of execution. (Correction, see finding
below: `mean_plan_time` in `pg_stat_statements` is per *plan*, not per call; the per-call reading in the first
version of this note was wrong. What is true is the total: planning still cost more than execution.)

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
Planning still 0.50 ms/req, i.e. 300 ms/s. Probed where it comes from, see next finding.

### Finding: half of all planning is one query with literal ids — go-vikunja/vikunja#3776

Method: `log_statement = all` for 15 s under a 300-user probe, then `pg_stat_statements` with the `plans` column
(now archived by `collect-run.sh` too). Prepared statements *are* reused by pgx (12,941 named executes, 15
unnamed, 320 distinct texts server-wide, so the 512-entry cache is not the problem). Over 75 s: 110,790 calls,
11,109 plans, 5,128 ms planning vs 9,240 ms execution. Ranked by planning time:

| calls | plans | plan ms | exec ms | statement |
|---|---|---|---|---|
| 1,985 | 1,985 | 2,558 | 166 | `WITH RECURSIVE project_hierarchy … WHERE t.id IN (<literal ids>)` — subscriptions for a task read |
| 531 | 544 | 529 | 58 | same CTE, project variant |
| 258 | 258 | 213 | 11 | same CTE, project variant, user-only |
| 17 | 17 | 189 | 12 | `SELECT column_name, column_default …` — xorm schema introspection, 17× in 75 s = the `vikunja healthcheck` compose probe every 5 s opens a fresh engine |
| 1,480 | 1,484 | 118 | 10 | `task_attachments WHERE task_id IN ($1…$N)` — parametrised, but the plancache prefers custom plans; cheap |

`pkg/models/subscription.go` (`getSubscriptionsForEntitiesAndUser`) interpolates the entity ids and the user
id into the SQL text (`entityIDString`, `sUserCond`). Every `GET /tasks/{id}` is a statement Postgres has never
seen: no prepared statement reuse, planner on every call, 1.3 ms each for 0.08 ms of execution. Fix: bind them
as parameters (PR #3776). Expected: roughly half of the remaining planning time, ~150 ms/s of DB CPU at 3000 users.
The pr-3776 image is main + this fix *without* the token cache (#3774 is not merged), so its run is compared on
DB-side numbers only.

### 10. Unstable with pgx, without the token cache — `runs/unstable-pgx/2026-09-06_01-08-54`

CI unblocked; `vikunja/vikunja:unstable` = `v2.6.0-141-g8ba3bbdf` (pgx merged). Same deployment config as
conn-lifetime. This isolates the two code changes: pgx alone brings the DB from 82 % to 46 % (planning 2.36 → 0.53
ms/req); the token cache (#3774) alone is Vikunja host 79 % → 52 % and p50 21 → 13 ms, p95 55 → 20 ms.

### 11. Subscription ids as parameters (#3776) — `runs/sub-params/2026-09-06_01-23-01`

Image `pr-3776` = unstable + #3776, no token cache, so compare with unstable-pgx. Planning 0.53 → 0.15 ms/req
(324 → 77 ms/s), DB CPU 46 → 42 %, p99 84 → 73 ms. Execution went 0.72 → 0.84 ms/req: the CTE now runs a generic
plan instead of one tailored to a literal id, which is a little slower per call. Net DB CPU still down. (The local
wrapper was OOM-killed mid-run by the workstation; the remote run completed and was archived by hand, hence the
run id equals the locust start time.)

### 12. Capacity: 6000 users — `runs/cap6000/2026-09-06_01-51-04`

pgx + token cache (pr-3774), pool 32, 1 h lifetime, GOGC 400, jit off. 711k requests, 3 failures, 1,242 rps
steady, p50 24 / p95 85 / p99 130 ms. DB at 85 % (load1 16), Vikunja at 79 %: this is the ceiling of two ccx23s
with the current code. At the start of the session the same boxes were at 73–82 % with **half** the load
(3000 users, 600 rps) and, with API-token bots, p50 73 ms. Capacity roughly doubled; #3776 (not in this image)
takes another ~0.4 ms of planning per request off the DB.

### Finding: the grants CTE seq-scans `projects` on every recursion level — go-vikunja/vikunja#3777

`EXPLAIN (ANALYZE, BUFFERS)` of the grants CTE for the heaviest team user: 0.68 ms, 197 buffers, of which 120
are a `Seq Scan on projects` (1,449 rows) hashed for the recursive join on `parent_project_id`. Roots store NULL
(done in `fc78cd3ea`), but the partial index from the 08-30 report's rec 2a was never added, so the planner still
prefers a seq scan over the full index. With `CREATE INDEX … ON projects (parent_project_id) WHERE
parent_project_id IS NOT NULL` (100 rows) the recursive step becomes a bitmap index scan: 0.30 ms. The index is
measured live (created in `vikunja` and in the `vikunja_snap` template) in run `partial-index`; PR #3777 adds it as
a migration (Postgres + SQLite; MySQL has no partial indexes).

### 13. Partial parent index (#3777) — `runs/partial-index/2026-09-06_02-08-51` (kept)

Compare with conn-lifetime (same image and config). Grants CTE mean 0.32 → 0.19 ms (89 → 55 s total over the
run), DB exec 0.62 → 0.52 ms/req, DB CPU 44 → 42 %, p99 26 → 24 ms, 0 failures. The CTE is still 37 % of DB
execution time at 0.77 calls per request; the next step for it is a cross-request cache (see report).

## Where things stand (end of session)

At 3000 users, same hardware, same load shape: from p50 73 / p95 180 / p99 260 ms at 82 % DB / 82 % API
(baseline-v3) to p50 13 / p95 19 / p99 24 ms at 42 % / 52 % (partial-index, = pr-3774 + lifetime + index), and
#3776 not yet in that image. Capacity ~2× (6000 users at the old utilisation). Open PRs: #3774, #3775, #3776,
#3777. Next levers, in order: cross-request project-access cache; non-transactional read sessions (2.7 `BEGIN`
per request); a config-gated pprof endpoint to see what the remaining API-side CPU is.

### Cross-request project access cache — go-vikunja/vikunja#3780

Per the user: option (b), invalidation on every project/share/team write. Implementation: xorm `After*` hooks on
`Project`, `ProjectUser`, `TeamProject`, `TeamMember`, `Team` (xorm runs them after commit, so no pre-commit
data can be re-filled under the new generation); per-user invalidation where the write only concerns one user,
a new generation for structural changes; sessions that wrote bypass the memo (they may see their own
uncommitted grants); generation published via keyvalue and pulled ≤ 1/s for replicas, 30 s TTL as the bound.
`pkg/models` and the project/team/task web tests pass. Combined test build with all five PRs: #3779.

### 14. All five PRs together — `runs/combined/2026-09-06_10-05-12` (image pr-3779, `ea603a21a`)

p50 11 / p95 17 / p99 22 ms, DB 37 %, Vikunja 50 %, planning 0.14 ms/req, 2 failures (the #3697 index race).
Access cache hit rate only ~63 % (grants CTE 281k → 104k calls): `updateProjectLastUpdated`
(`pkg/models/project.go:1302`, 14 call sites, every task write) does `Cols("updated").Update(project)` with a bean
that carries the loaded `ParentProjectID`, so the `AfterUpdate` hook takes it for a re-parent and starts a new
generation. Fix (for #3780, branch owned by the user now): touch `updated` through a hook-less bean, e.g. a
`projectTouch{Updated time.Time}` with `TableName() = "projects"`. Expected hit rate then > 95 %.

### 15. All five PRs, 6000 users — `runs/combined-cap6000/2026-09-06_10-18-07`

1,251 rps, p50 14 / p95 41 / p99 66 ms, **0 failures**, DB 56 % (load1 4.0), Vikunja 77 %. Same load as `cap6000`
(pgx + token cache only): p95 85 → 41, p99 130 → 66, DB 85 → 56 %. The API host is now the first wall (PBKDF2 gone,
so it is JSON, routing and the ~18 statements per request); the DB has headroom again.

Stacked PR #3783 (hook-less project timestamp touch) is merged into #3779 together with the user's keyvalue
refactor of #3780 (`03f627fd4`); next combined run on head `7a6414d20` once its image is built.

### 16. Combined with #3783 — `runs/combined-v2/2026-09-06_10-48-59`

Grants CTE 281k → 25k calls (≈ 91 % cache hits; the rest are real invalidations from project creates and
TTL expiry), now 7 % of DB execution. DB exec 0.53 → 0.48 ms/req, DB load1 2.3 → 1.5, 0 failures. Latency did not
move (11 / 17 / 22 ms): at 3000 users the DB is no longer on the request path's critical side; the API host
(50 %, 77 % at 6000 users) is. Next lever there needs a profile, i.e. a config-gated pprof endpoint.

### Enabling step for the API side — go-vikunja/vikunja#3785

The API host is the first wall now and nothing can be profiled from outside (stripped binary, scratch image).
#3785 adds `metrics.pprof` (default off, needs `metrics.enabled`, behind the metrics basic auth when set) mounting
Go's pprof at `/debug/pprof/`. The test deployment sets `VIKUNJA_METRICS_PPROF=true`; the combined branch #3779
(head `f3bb05960`) includes it, so the next combined run gets a 30 s CPU profile mid-run. #3776 has meanwhile
been merged into main by the user.

### First API-side CPU profile (pr-3779 `f3bb05960`, 30 s at t=240 s of `combined-profile`) — go-vikunja/vikunja#3786

45 s of samples on 4 cores (151 %). Where it goes:

| share | what | lever |
|---|---|---|
| 28 % | `Syscall6` — network I/O, mostly DB round trips (~14 statements + 4 transactions per bot request) | fewer statements per request |
| 26 % cum | `v2.tasksRead` → `models.addMoreInfoToTasks` 21 % | the task read fans out into assignees, labels, attachments, reminders, favorites, relations, users, project… one query each |
| 5.3 % | `db.isWriteStatement`: two regexps on every SQL statement (session-cache write hook) | #3786 byte scan |
| 4.2 % | xorm `postgresSeqFilterConvertQuestionMark`: rewriting `?` → `$n` on every statement | xorm-level; a per-statement text cache in xorm would remove it |
| 2 % | `log.XormLogger.Infof` → `fmt.Sprintf` of every statement although database logging is off | #3786 level check first |
| 2.7 % cum | `encoding/json` marshalling | expected |

Statement sequence of one `GET /tasks/{id}` with an API token (from `log_statement = all`): `begin; api_tokens;
users; rollback` (token middleware), `begin; users; rollback` **twice** (`GetAuthFromClaims` reloads the owner for
the metrics middleware and again for the handler although `api_user` is in the context), then the handler's
transaction with ~11 selects (task, project, task again, assignees, labels, attachments, users, reminders,
favorites, project again, relations). #3786 drops the two user lookups; the remaining duplicates (task and
project loaded twice) are the next candidates.

### Second profile (pr-3779 `b089ac163` = + #3786, run `combined-v3`)

Total samples 45.4 → 41.0 s per 30 s. `GetAuthFromClaims` (9.2 % cum) and the xorm logger formatting (2 %) are
gone. `isWriteStatement` was still 5 %: the first fix only removed the regexp for the leading keyword, but every
recursive CTE is a `WITH` statement of several kilobytes and the CTE regexp scanned all of it. Follow-up commit on
#3786: whole-word scan, same boundary rules, no regexp at all. `postgresSeqFilterConvertQuestionMark` (xorm's
`?` → `$n` rewrite, 4 %) is the last generic per-statement cost and lives in xorm.

### 17. Combined with #3786 — `runs/combined-v3/2026-09-06_11-43-28`

Statements per request 18.0 → 14.6 (the two `users` lookups and their transactions per bot request are gone),
API host 50 → 45 %, container 1.75 → 1.55 cores, p50 11 → 10 ms, 0 failures. Second profile in the run dir.

### Duplicate single-row lookups — go-vikunja/vikunja#3787

From the statement log: a task read loads the task twice (`Task.CanRead`, then `ReadOne`) and its project twice
(permission check, then `addMoreInfoToTasks`); across all requests 1.9 `users`, 1.2 `projects`, 0.8 `tasks`
lookups by id per request. #3787 routes `GetTaskByIDSimple`, `GetProjectSimpleByID`, `GetProjectsMapByIDs`,
`user.GetUserByID`, `user.GetUsersByIDs` through the per-session memo (drops itself on any write in that session;
callers get copies). Expected: 2–3 statements fewer per request. Merged into #3779 (`cb03108cc`) for the next
combined run; `combined-v4` (running) measures the WITH-scan fix on its own first.

### Third profile (pr-3779 `eee403ef8` = + WITH word scan, run `combined-v4`)

Samples per 30 s: 45.4 → 41.0 → **37.1 s** across the three profiles (−18 % API CPU at equal load).
`isWriteStatement` 5.6 % → 0.5 %, regexp no longer in the profile. What is left: syscalls 31 % (round trips),
`tasksRead` 22.6 % cum, xorm `?`→`$n` rewrite 3.8 %, allocation 6.7 %, JSON 2.7 %.

### 18. Combined with #3787 — `runs/combined-v5/2026-09-06_12-15-02`

Statements per request 14.6 → 13.2, API host 43 → 41 %, container 1.50 → 1.42 cores, profile samples per 30 s
37.1 → 35.4 s, 0 failures. Latency unchanged at 9 / 16 / 22 ms: at 3000 users the request path is now dominated by
the remaining ~13 round trips, not CPU.

## Where things stand (end of session, second part)

Same hardware and load shape as baseline-v3 (p50 73 / p95 180 / p99 260 ms at 82 % DB / 82 % API):
**p50 9 / p95 16 / p99 22 ms at 39 % DB / 41 % API.** API-side CPU per request down 22 % across the three profiles.
Open PRs: #3774, #3775, #3777, #3780 (+ #3783 stacked), #3785, #3786, #3787; #3776 merged; #3779 = all of them.
Next levers, in order: fewer queries per task read (`addMoreInfoToTasks` fans out into one query per related
entity even for a single task; ~11 selects), xorm's `?`→`$n` rewrite per statement (xorm-level), then JSON.

### 19. Capacity on the final image, 6000 users — `runs/combined-v5-cap6000/2026-09-06_12-28-53`

1,259 rps, p50 9 / p95 21 / p99 34 ms, 4 failures (all the #3697 index race), DB 43 % (load1 2.3), API 65 %.
Against the first 6000-user run today (pgx + token cache only): p95 85 → 21, p99 130 → 34, DB 85 → 43 %,
API 79 → 65 %. Against the start of the session, where 3000 users already put both boxes at 73–82 %: twice the
load at roughly half the utilisation, with a tenth of the p95.

### 20. 9000 users — `runs/cap9000/2026-09-06_13-57-32`

Locust now runs with `--processes 4` (one gevent process was at ~1 core for 6000 users). 1,873 rps, p50 11 /
p95 68 / p99 130 ms, API host 83 % avg / 92 % max, DB 68 % / 82 %, DB exec per request 0.38 → 0.45 ms (contention).
The API host is the wall; p99 < 50 ms holds to roughly 7,000–7,500 users on the current code and a ccx23.

Target from the user: 10,000 users at p99 < 50 ms. Two ways, probably both: (a) API host to 8 dedicated cores
(ccx33; CPU per request is constant, 10k would sit at ~46 % of 8 cores) and DB to ccx33 as well since 70 %+ on the
DB is where per-statement execution starts to stretch; (b) fewer round trips per request on the code side
(task read fan-out, ~9 selects for one task; xorm `?` rewrite; JSON).

### 21. 10,000 users on ccx33 + ccx33 — `runs/cap10000/2026-09-06_14-41-42`

Infra recreated (`teardown.sh`, `setup.sh` with `TYPE_DB=ccx33 TYPE_VIKUNJA=ccx33`, now the defaults in
`config.sh`; Postgres `shared_buffers` 8 GB, `effective_cache_size` 24 GB, 8 workers; pool 48; `GOMEMLIMIT` 8 GiB;
image pr-3779). Seed took 55 s instead of 158 s. Result: 2,107 rps, **p50 6 / p95 10 / p99 14 ms**, API host
60 % avg / 84 % max (4.45 cores), DB 25 % avg (1.66 cores), DB exec 0.23 ms/req (no contention at all). The
user's target (10k users, p99 < 50 ms) is met with ~3× headroom on the tail. The DB upgrade was not needed for
10k: at 25 % of 8 cores it would be ~50 % of a ccx23. Loadgen (cx33, 4 locust processes) at 42 %: fine to ~15k,
then it needs a bigger box or a second one.

### 22. Ceilings at p99 < 50 ms — `runs/cap14000/…`, `runs/db23-cap12000/…`

Load generator resized to cx43 (8 vCPU) with 8 locust processes; `hcloud server change-type` to a smaller type
is refused with `--keep-disk`, so the ccx23-DB variant was a full recreate (`TYPE_DB=ccx23 ./setup.sh`).

| setup | max users | rps | p50 / p95 / p99 | wall |
|---|---|---|---|---|
| ccx33 API + ccx33 DB | ~14,000 | 2,947 | 6 / 20 / 45 ms | API 76 % avg / 93 % max |
| ccx33 API + ccx23 DB | ~12,000 | 2,518 | 9 / 28 / 47 ms | DB 87 % / 95 %, load1 13, exec/req 0.27 → 0.67 ms |

Both numbers sit at the edge; plan with 13k and 11k. Infra defaults now: DB ccx23 (conf halved), API ccx33,
loadgen cx43, matching the running stack.

### 23. Big boxes: API ccx53 (32 cores / 128 GB), DB ccx43 (16 / 64), loadgen ccx43 with 16 locust processes

Sizing from the per-request constants (2 ms API core, 1 ms DB core): ~40k users expected before the API knee.
First run, 20,000 users, pool 48 — `runs/big-cap20000/2026-09-06_16-08-58`: 3,603 rps (demand ~4,200), p50 200 / p95 690 / p99 1,000 ms with the
API host at 40 % and the DB at 37 %. Not CPU: `pg_stat_activity` showed **44 backends idle in transaction at peak
and 7 active**, i.e. the 48-connection pool full of requests holding their transaction across API work and ~13
round trips (bot requests hold two: token auth, then the handler). The DB itself was idle. Pool raised to 192
(max_connections 200) and the runs repeated as `pool192-cap*`. The structural fix is the old report's code rec 1:
read-only handlers should not `BEGIN`; at this scale connection hold time, not CPU, is the limit.

Pool 192 with the default `maxidleconnections` 50 — `runs/pool192-cap20000/2026-09-06_16-23-33`: demand met (4,056 rps) but p50 57 / p99 180 ms, DB
planning 0.13 → 0.75 ms per request, DB load1 20 on 16 cores, idle backends capped at 47 and 171 idle in
transaction at peak. Connections above the 50th are closed when idle and reopened (and re-prepared) on the next
burst. `VIKUNJA_DATABASE_MAXIDLECONNECTIONS=192` for the next runs; default changed to 100 (= max open) in #3775.

Pool 192, idle 192 — `runs/idle192-cap20000/2026-09-06_16-37-47`: 4,145 rps, p50 32 / p95 71 / p99 94 ms, planning back to 0.15 ms/req, both hosts
at 41 %. Still 170 idle in transaction at peak vs 13 active: average connection hold time ≈ 9 ms per request
(one transaction per request across ~13 round trips and the API's own work), so bursts fill any pool near 200
while the DB idles. Next: `max_connections` 500, pool 400 (`pool400-cap*`). The structural answer stays the
same: stop holding a transaction per request.

### Read paths without a transaction — go-vikunja/vikunja#3790

`db.NewReadSession()`: session memo attached, no `Begin()`; `Commit`/`Rollback` are no-ops on it. Used by
`DoReadOne`, `DoReadAll` and `ValidateAPITokenString`. A request no longer holds a pooled connection across its
own work; each statement borrows one for its duration. This is the old report's code rec 1 and the direct answer
to the pool saturation at 20k users. Merged into #3779 (`c1ed33d39`) together with the idle-connection default
from #3775; measured next on the big boxes with pool 400.
