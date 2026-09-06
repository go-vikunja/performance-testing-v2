# Vikunja API performance: tuning session 2026-09-05/06

Run-by-run log with every number: `NOTES.md` (repo root). Raw data per run: `runs/<name>/<timestamp>/`
(locust csv/html, Grafana panels, `pg_stat_statements` dumps, CPU profiles where taken).

## Summary

Same two 4-core boxes, same load shape, before and after:

| 3000 simulated users | start of session | end of session |
|---|---|---|
| p50 / p95 / p99 | 73 / 180 / 260 ms | 9 / 16 / 22 ms |
| DB host CPU / API host CPU | 82 % / 82 % | 39 % / 41 % |
| statements per request | 18.5 | 13.2 |
| DB planning per request | 2.39 ms | 0.18 ms |

The target of 10,000 users at p99 < 50 ms is met with an 8-core API host: p99 14 ms at 2,107 rps. Measured
ceilings for p99 < 50 ms are ~14,000 users with both boxes on 8 cores and ~12,000 with the database on 4 cores.

Nine Vikunja changes came out of it, one merged (#3721 pgx, #3776), the rest as draft PRs measured individually
and together (#3779). Two of the biggest costs were invisible to the earlier reports because the load model did
not exercise them: API-token authentication and the connection lifetime default.

## Setup and method

- Hetzner Cloud: db + vikunja (ccx23, 4 dedicated cores / 16 GB, later ccx33 with 8 / 32), monitoring cx23,
  load generator cx33 (later cx43). Postgres 18 with `pg_stat_statements` incl. planning time, Prometheus,
  Grafana. Vikunja `v2.6.0-113` at the start, `v2.6.0-141` unstable plus PR preview images later.
- Seed: 100 accounts × 6 projects × 80 tasks, 600 labels, teams of 5 sharing one project. Every run starts from a
  snapshot of the seeded database (template copy, seconds), so runs do not drift.
- Load: `Worker`, `Glancer`, `IntegrationBot` classes derived from Vikunja Cloud access logs; 3000 users, spawn
  25/s, 10 min for comparisons; 6000–14,000 users for capacity. "Steady" numbers are the median of locust's
  per-second percentiles over the second half of the full-load window. Host CPU is the Prometheus average over
  the same window.
- Two load-model corrections were made at the start; numbers before and after them are not comparable:
  1. bcrypt cost 4 on the test deployment. The 25 logins/s ramp was a cost-11 bcrypt benchmark that pinned the
     API host for the whole spawn phase; every ramp number in earlier reports is that.
  2. Bots authenticate with API tokens (65 % of production requests do) and returning users refresh their JWT
     instead of logging in. This alone made everything 4–5× more expensive and exposed finding 2.

## Results

All runs on the pr-3779 image contain every PR listed below at the time of the run.

| run | users | boxes (db / api) | rps | p50 / p95 / p99 ms | DB exec + plan ms/req | DB CPU | API CPU |
|---|---|---|---|---|---|---|---|
| `baseline-v3` — lib/pq, v2.6.0-119 | 3000 | ccx23 / ccx23 | 605 | 73 / 180 / 260 | 0.93 + 2.39 | 82 % | 82 % |
| `token-cache` — pgx (#3721) + token cache (#3774) | 3000 | ccx23 / ccx23 | 634 | 13 / 25 / 110 | 0.67 + 0.82 | 48 % | 53 % |
| `conn-lifetime` — + lifetime 10 s → 1 h (#3775) | 3000 | ccx23 / ccx23 | 629 | 13 / 20 / 26 | 0.62 + 0.50 | 44 % | 52 % |
| `sub-params` — + subscription ids as parameters (#3776), no token cache | 3000 | ccx23 / ccx23 | 627 | 20 / 49 / 73 | 0.84 + 0.15 | 42 % | 78 % |
| `partial-index` — + partial parent index (#3777) | 3000 | ccx23 / ccx23 | 636 | 13 / 19 / 24 | 0.52 + 0.48 | 42 % | 52 % |
| `combined-v2` — + access cache (#3780, #3783) | 3000 | ccx23 / ccx23 | 633 | 11 / 17 / 22 | 0.48 + 0.15 | 37 % | 50 % |
| `combined-v4` — + per-request overhead (#3786) | 3000 | ccx23 / ccx23 | 637 | 9 / 16 / 22 | 0.55 + 0.17 | 39 % | 43 % |
| `combined-v5` — + session memo (#3787), all PRs | 3000 | ccx23 / ccx23 | 638 | 9 / 16 / 22 | 0.55 + 0.18 | 39 % | 41 % |
| `combined-v5-cap6000` | 6000 | ccx23 / ccx23 | 1,259 | 9 / 21 / 34 | 0.38 + 0.11 | 43 % | 65 % |
| `cap9000` | 9000 | ccx23 / ccx23 | 1,873 | 11 / 68 / 130 | 0.45 + 0.14 | 68 % | 83 % |
| `cap10000` | 10,000 | ccx33 / ccx33 | 2,107 | 6 / 10 / 14 | 0.23 + 0.08 | 25 % | 60 % |
| `cap14000` | 14,000 | ccx33 / ccx33 | 2,947 | 6 / 20 / 45 | 0.27 + 0.09 | 39 % | 76 % |
| `db23-cap12000` | 12,000 | ccx23 / ccx33 | 2,518 | 9 / 28 / 47 | 0.67 + 0.18 | 87 % | 50 % |

Configuration steps measured on the way (kept unless noted): pool 100 → 32 (same throughput, p99 halved, DB
load1 14.6 → 8.1); `jit = off` and no parallel workers (within noise, kept); `GOGC=400` (−3 % API CPU for
+400 MB RSS, kept); `plan_cache_mode = force_generic_plan` (reverted, makes the recursive CTE's plan 2.7× more
expensive to build).

## Findings, by impact

1. **Every statement was planned from scratch.** With lib/pq, Postgres spent more CPU planning than executing
   (2.4 vs 0.9 ms per request). #3721 (pgx, merged) fixed it: DB host 82 → 46 %.

2. **API-token authentication ran PBKDF2-SHA256 × 10,000 on every request** (`models.HashToken`), ~3 ms of CPU
   each, plus its own transaction before the handler. With bots on tokens the API host went 51 → 82 % and bot p50
   20 → 92 ms. #3774 remembers verified tokens in-process (digest → id, row reloaded by id so revocation still
   applies). API host 79 → 52 %, bot p50 → 14 ms.

3. **`database.maxconnectionlifetime` defaults to 10 seconds.** Every pooled connection is reconnected every
   10 s (verified live: all 32 backends < 9.3 s old), which discards pgx's statement cache and the plan cache.
   With 1 h: p99 110 → 26 ms, planning −40 %. #3775 changes the default to 30 min.

4. **The subscription lookup interpolated ids into SQL** (`pkg/models/subscription.go`), so every
   `GET /tasks/{id}` was a statement Postgres had never seen: planned every call, 1.3 ms planning for 0.08 ms
   execution, half of all remaining planning. #3776 (merged) binds them: planning 0.53 → 0.15 ms per request.

5. **The recursive access CTE seq-scanned `projects` at every recursion level.** Top-level projects store NULL
   as parent, but without a partial index the planner hashed all projects for the recursive join. #3777 adds
   `projects (parent_project_id) WHERE parent_project_id IS NOT NULL`: CTE 0.32 → 0.19 ms.

6. **The access CTE ran once per request** (per-session memo only), half of DB execution time. #3780 keeps the
   resolved map per user in keyvalue, invalidated by xorm after-commit hooks on projects, shares and teams; #3783
   stops the per-task-write project timestamp touch from invalidating it. 281k → 25k calls per run.

7. **Per-request overhead found by the first CPU profile** (#3785 adds the `metrics.pprof` endpoint): the
   session-cache write hook ran regexps on every SQL statement (5 % of API CPU, the CTE texts are kilobytes), the
   xorm logger formatted every statement although database logging is off (2 %), and `GetAuthFromClaims`
   reloaded the token owner in a fresh transaction twice per request. #3786: statements per request 18.0 → 14.6,
   API host 50 → 43 %. Three profiles: 45.4 → 41.0 → 37.1 s of samples per 30 s window.

8. **Duplicate single-row lookups.** A task read loaded the task and its project twice; 1.9 `users` lookups per
   request. #3787 memoizes the id lookups per session (the memo drops itself on writes). 14.6 → 13.2 statements.

9. Task index race (`UQE_tasks_tasks_project_index` on concurrent creates, 1–8 per run): fixed by #3697.

Checked and rejected: a closure table for the project tree. Measured on the live database, the recursive step is
per-iteration overhead, not depth (a 10-deep chain added nothing measurable); with the cache the CTE is ~1.5 %
of one DB core, and the closure join would save ~0.3 ms per cold fill for a new table, four write paths and a
worse failure mode.

## Capacity and sizing

| configuration | max users at p99 < 50 ms | rps | limiting host |
|---|---|---|---|
| ccx23 db + ccx23 api | ~7,500 (9,000 gives p99 130 ms) | ~1,550 | API at ~80 % |
| ccx23 db + ccx33 api | ~12,000 (p99 47 ms) | 2,518 | DB at 87 % / 95 % peaks |
| ccx33 db + ccx33 api | ~14,000 (p99 45 ms) | 2,947 | API at 76 % / 93 % peaks |

Plan with 10–15 % below those numbers. API CPU per request is constant across sizes (about 0.45 ms of a core),
so the API host sizes linearly with users; the database is fine up to ~10k on 4 cores and needs 8 cores beyond
~11k, where per-statement execution starts to stretch under contention (0.27 → 0.67 ms per request).

For reference, Vikunja Cloud averages ~3 requests per second; 3000 simulated users are ~600.

## Hosting recommendations

- `database.maxopenconnections`: 2–3× DB cores (32 for 4 cores, 48 for 8), not 100.
- `database.maxconnectionlifetime`: ≥ 30 min until #3775 lands (the default is 10 s).
- Postgres: `jit = off`, `max_parallel_workers_per_gather = 0`; `shared_buffers` 25 % of RAM. Everything is in
  cache at this size; IO never showed up.
- `GOGC=400` with a `GOMEMLIMIT` is a few percent of API CPU for RAM you have anyway.
- Load generator: 4 locust processes per 4 vCPUs; one cx43 with 8 processes carries 14k simulated users at 33 %.

## Pull requests

Merged: #3721 (pgx), #3776 (subscription parameters). Open, in merge order: #3774, #3775, #3777, #3780 then #3783
(stacked), #3785, #3786, #3787. #3779 is the combined test build of all of them; close it after merging. The test
deployment pins `ghcr.io/go-vikunja/vikunja:pr-3779` in `infra/config.sh`; switch back to `unstable` afterwards.

## What is left

1. **Fewer queries per task read.** `addMoreInfoToTasks` fans out into one query per related entity (assignees,
   labels, attachments, reminders, favorites, relations, users) even for a single task; ~9 selects plus the
   auth transaction. Round trips are now the largest share of API CPU (31 % in syscalls).
2. **xorm's `?` → `$n` rewrite** on every statement (4 % of API CPU), an xorm-level cache by statement text.
3. JSON and allocation (~10 % together); the next profile after 1 will say which.
4. A `/health` HTTP probe instead of the `healthcheck` subcommand, which boots a full engine incl. schema
   introspection on every probe.

## Test-side notes

- `run-test.sh` restores the seeded database from the `vikunja_snap` template before every run; `reset.sh`
  creates it after seeding. `collect-run.sh` archives a finished run on its own. `redeploy.sh <role>` re-applies
  one host's compose or swaps `VIKUNJA_IMAGE`.
- `pg_stat_statements.mean_plan_time` is per plan, not per call; the archive now includes `plans` next to `calls`.
- Preview images report a wrong version string; check the image label `org.opencontainers.image.revision`.
- `hcloud server change-type` to a smaller type is refused with `--keep-disk`; recreate instead.
- Fixed on the way: the Prometheus locust target rendered with an empty IP, the Vikunja healthcheck used `wget`
  (not in the image), the load generator ran out of ephemeral ports, a locust run that never exits is now killed
  90 s after it stops, and editing `run-test.sh` while a run is in progress corrupts it (bash reads scripts
  incrementally), hence the split into `collect-run.sh`.
