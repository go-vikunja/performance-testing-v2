# Capacity report: tuning session 2026-09-05/06

Full log with every run and the reasoning: `NOTES.md` (repo root). This report is the summary.

Infra unchanged: ccx23 db + ccx23 vikunja (4 dedicated cores / 16 GB each), postgres:18, seed 100 users × 6
projects × 80 tasks. All runs 3000 users, spawn 25/s, 10 min, classes `Worker Glancer IntegrationBot`, except the
capacity run (6000 users, 50/s). Vikunja from `v2.6.0-113` (session start) to `v2.6.0-141` unstable plus two PR
preview images.

## Two test-side changes first

1. **The login ramp was a bcrypt benchmark.** 25 logins/s × cost-11 bcrypt pinned the API host for the whole spawn
   phase; every ramp number in the earlier reports is that. The test deployment now runs
   `VIKUNJA_SERVICE_BCRYPTROUNDS=4` (not a recommendation for production, a way to see the rest).
2. **Bots now authenticate with API tokens, glancers refresh instead of logging in.** No class used API tokens
   before, although 65 % of production requests do. That change alone made everything 4–5× more expensive
   (see finding 2) and is the reason the earlier reports never saw the largest CPU consumer.

Runs before these changes are in `NOTES.md`; the table below starts after them.

## Numbers

Steady state = second half of the full-load window. CPU = host average over that window.

| run | code | change | rps | p50 / p95 / p99 ms | DB exec + plan ms/req | DB CPU | Vikunja CPU |
|---|---|---|---|---|---|---|---|
| `baseline-v3` | v2.6.0-119, lib/pq | pool 32, bcrypt 4, jit off | 605 | 73 / 180 / 260 | 0.93 + 2.39 | 82 % | 82 % |
| `gogc400` | v2.6.0-121 | + GOGC 400 / GOMEMLIMIT 4 GiB | 611 | 62 / 170 / 240 | 0.93 + 2.36 | 82 % | 80 % |
| `token-cache` | pr-3774 (pgx + token cache) | + pgx (#3721), verified-token cache (#3774) | 634 | 13 / 25 / 110 | 0.67 + 0.82 | 48 % | 53 % |
| `conn-lifetime` | pr-3774 | + connection lifetime 10 s → 1 h | 629 | 13 / 20 / 26 | 0.62 + 0.50 | 44 % | 52 % |
| `unstable-pgx` | v2.6.0-141 (pgx, no cache) | reference: main without #3774 | 626 | 21 / 55 / 84 | 0.72 + 0.53 | 46 % | 79 % |
| `sub-params` | pr-3776 (pgx + params, no cache) | + subscription ids as parameters (#3776) | 627 | 20 / 49 / 73 | 0.84 + 0.15 | 42 % | 78 % |
| `cap6000` (6000 users) | pr-3774 | capacity | **1,242** | 24 / 85 / 130 | 0.96 + 0.70 | 85 % | 79 % |
| `partial-index` | pr-3774 | + partial index on `projects.parent_project_id` (#3777) | 636 | 13 / 19 / 24 | 0.52 + 0.48 | 42 % | 52 % |
| `combined-v2` | pr-3779 (all PRs) | + access cache (#3780, #3783) | 633 | **11 / 17 / 22** | 0.48 + 0.15 | **37 %** | **50 %** |
| `combined-cap6000` (6000 users) | pr-3779 | all PRs, capacity | **1,251** | 14 / 41 / 66 | 0.47 + 0.15 | 56 % | 77 % |
| `combined-v3` | pr-3779 (+ #3786) | + per-request overhead from the first CPU profile | 640 | **10 / 16 / 22** | 0.53 + 0.17 | 39 % | **45 %** |

Same hardware, same load shape: from p50 73 ms at 82 % / 82 % to p50 11 ms at 37 % / 50 %. At 6000 users
(1,251 rps, 0 failures) the boxes sit at 56 % / 77 %, below what they needed for 3000 users at the start.

## Findings, by impact

1. **Every statement was planned from scratch (lib/pq).** Planning cost more DB CPU than execution (2.4 vs 0.9 ms
   per request). Fixed by #3721 (pgx, merged). DB host 82 → 46 %.
2. **API-token authentication ran PBKDF2-SHA256 × 10,000 on every request** (`models.HashToken`), ~3 ms of CPU each,
   plus its own transaction (4 statements) before the handler. With bots on tokens the API host went 51 → 82 % and
   bot p50 20 → 92 ms. #3774 remembers verified tokens in-process (digest → id, reload by id so revocation still
   applies). API host 79 → 52 %, p50 21 → 13 ms.
3. **`database.maxconnectionlifetime` defaults to 10 seconds.** Every pooled connection is reconnected every 10 s
   (verified: all 32 backends < 9.3 s old), which discards pgx's statement cache and the plan cache and costs the
   reconnects. 1 h: p99 110 → 26 ms, planning −40 %. #3775 changes the default to 30 min.
4. **The subscription lookup interpolates ids into SQL** (`pkg/models/subscription.go`), so every `GET /tasks/{id}`
   is a never-seen statement: planned every call, 1.3 ms planning for 0.08 ms execution, half of all remaining
   planning. #3776 binds them as parameters. Planning 0.53 → 0.15 ms/req.
5. **The grants CTE seq-scans `projects` at every recursion level.** Top-level projects store NULL as parent, but
   without a partial index the planner hashes all 1,449 projects for the recursive join (120 of 197 buffers).
   #3777 adds `projects (parent_project_id) WHERE parent_project_id IS NOT NULL`: CTE 0.32 → 0.19 ms mean under
   load, DB exec 0.62 → 0.52 ms/req.
6. **The grants CTE ran once per request** (per-session memo only). #3780 keeps the resolved access map per user
   across requests (keyvalue-backed, invalidated by xorm after-commit hooks on projects / shares / teams), #3783
   stops the per-task-write project timestamp touch from invalidating it. 281k → 25k calls per run, DB load1 2.3 → 1.5.
7. **API-side per-request overhead, from the first CPU profile** (#3785 adds the profiler endpoint): the
   session-cache write hook ran two regexps on every statement (5 % of API CPU), the xorm logger formatted every
   statement although database logging is off (2 %), and `GetAuthFromClaims` reloaded the API token's owner in a
   fresh transaction twice per request (9 % cum). #3786: statements per request 18.0 → 14.6, API host 50 → 45 %.
8. **Pool 100 → 32** on a 4-core DB: same throughput, p99 halved, DB load1 14.6 → 8.1. Hosting-side only.
9. `jit = off`, no parallel workers, `GOGC=400`: each a few percent, kept as deployment config.
10. `plan_cache_mode = force_generic_plan`: tried, reverted (makes the recursive CTE's plan 2.7× more expensive).
11. Task index race (`UQE_tasks_tasks_project_index` 500s on concurrent creates): 1–4 per run, fixed by #3697.

## What is left (ordered)

1. **Merge #3774, #3775, #3777, #3780, #3783, #3785, #3786** (#3776 is merged; measured together as #3779: p50 10 ms,
   DB 39 %, API 45 % at 3000 users; 1,251 rps at 6000 before #3786). Close #3779 afterwards.
2. **What the API host still spends its CPU on** (profile in `runs/combined-v3/…/cpu-profile-t240-30s.pb.gz`):
   26 % network syscalls (≈ 14 statements + 2 transactions per request), 28 % cum in `tasksRead` →
   `addMoreInfoToTasks` (one query per related entity; the task and its project are loaded twice per read),
   4 % xorm's `?` → `$n` rewrite on every statement (xorm-level). Next: fewer queries per task read.
3. **API-token path opens its own transaction** (`auth.ValidateAPITokenString`): BEGIN, token, user, COMMIT before
   the handler. A non-transactional read session in `pkg/db` would drop 2 round trips per bot request. Same for
   read-only handlers in general (`db.NewSession()` always `Begin()`s): 2.7 transactions per request today.
4. **Healthcheck subcommand boots a full engine** incl. schema introspection each time (17× in 75 s at the 5 s
   compose interval). Test infra now probes every 30 s; a `/health` HTTP probe would be cheaper for everyone.
5. A config-gated pprof endpoint would allow profiling the remaining API-side CPU (binary is stripped, image is
   scratch; nothing can be profiled from outside).

## Hosting recommendations

- `database.maxopenconnections`: 2–3× DB cores (32 for 4 cores), not 100.
- `database.maxconnectionlifetime`: ≥ 30 min until #3775 lands.
- Postgres: `jit = off`, `max_parallel_workers_per_gather = 0` for this workload.
- Both boxes reach 80–85 % at 6000 users / 1,250 rps with pgx + token cache; the DB is the first wall again.

## Test-side notes

- `run-test.sh` now restores the seeded database from the `vikunja_snap` template before every run (seconds), so
  runs no longer drift; `reset.sh` creates the snapshot after seeding.
- `collect-run.sh` archives a finished run on its own (used twice when the local wrapper was OOM-killed by the
  workstation, not by the test).
- `redeploy.sh <role>` re-applies one host's compose/config; `VIKUNJA_IMAGE=… ./redeploy.sh vikunja` swaps images.
- `pg_stat_statements.mean_plan_time` is per plan, not per call; use `plans` vs `calls` (now archived) to see how
  often a statement is planned.
- Preview images report a wrong version string (`git describe` of the base); check the image label
  `org.opencontainers.image.revision`.
