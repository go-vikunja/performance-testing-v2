# Capacity report: 500 / 1500 / 3000 concurrent users (2026-08-29)

Runs: `baseline/2026-08-29_14-39-29` (500), `baseline/2026-08-29_15-03-40` (1500), `baseline/2026-08-29_15-17-00` (3000).
Same seed (100 accounts, 700 projects, 48k tasks), classes `Worker Glancer IntegrationBot`, 10 min each,
Vikunja `v2.5.0-249-gc0ebf473` on ccx23 (4 dedicated vCPU / 16 GB), Postgres 18 on ccx23, pool `maxopenconnections=100`.

## Numbers

Steady state = after the ramp-up, from `locust_stats_history.csv`; averages from Prometheus over the same window.

| | 500 users | 1500 users | 3000 users |
|---|---|---|---|
| spawn rate | 10/s | 25/s | 25/s |
| requests / rps (whole run) | 63,974 / 107 | 180,589 / 301 | 266,472 / 162* |
| steady-state rps | ~107 | ~310 | ~510 |
| steady-state p50 / p95 / p99 ms | 17 / 37 / 320 | 13 / 28 / 50 | 200 / 1,900 / 2,500 |
| ramp-up peak p50 / p95 ms | 78 avg | 3,300 / 13,000 | 6,900 / 26,000 |
| failures | 4 (test noise) | 0 | 9 (5 timeouts, 3× HTTP 500 on task create) |
| DB host CPU avg / max | 28 % / 30 % | 45 % / 63 % | 78 % / 95 % |
| Postgres container cores | 0.96 | 1.65 | 3.03 (of 4) |
| DB load1 avg / max | 1.6 / 5 | 4.9 / 22 | **35 / 49** |
| Vikunja host CPU avg / max | 23 % / 49 % | 42 % / 100 % | 61 % / 100 % |
| Vikunja container cores | 0.70 | 1.49 | 2.28 |
| Vikunja RSS | 213 MB | 272 MB | 430 MB (max 576) |
| goroutines | 1.2k | 3.0k | 5.9k (max 7.1k) |
| Postgres backends avg / max | 10 / 15 | 21 / 102 | **78 / 102** |
| DB exec time ms per second | 147 | 418 | 2,541 (max 9,600) |
| statements per request | 15 | 14.9 | 14.7 |
| avg ms per statement | 0.10 | 0.105 | **0.38** |
| DB exec ms per request | ~1 | 1.6 | 5.6 |
| cache hit / block IO / lock waits | 100 % / 0 / 0 | 100 % / 0 / 0 | 100 % / 0 / 0 |

\* the 3000-user run's whole-run rps is low because locust hung for 17 min at shutdown with one user left (run
window 29 min instead of 10). Steady state is the number that matters.

## What happens

1. **Up to ~1500 users the system is comfortable.** rps scales linearly with users (~0.2 rps per simulated user),
   steady-state p95 stays under 30 ms, no resource above 50 %. The only ugly part is the ramp-up: 25 logins per
   second = 25 bcrypt hashes per second saturates the Vikunja host (4 cores at 100 %) and every request queues
   behind them (p95 13 s during the ramp). Steady-state login is 160-200 ms.
2. **At 3000 users Postgres CPU is the wall.** The DB box runs at 78 % average / 95 % peak with load1 35-49 on
   4 cores: 100 connections from the pool are all active and fight for 4 CPUs. Per-statement time goes
   0.10 → 0.38 ms purely from contention (no IO, no lock waits, 100 % cache hits), so DB time per request goes
   1 → 5.6 ms and the queueing on top pushes p50 to 200 ms and p95 to ~2 s. Vikunja itself still has headroom
   (2.3 of 4 cores, 430 MB RSS, 6k goroutines).
3. **The DB work is dominated by a handful of statements, all permission/project-tree related** (see
   `pg-top-statements.txt` of the 3000 run, total ms / calls / mean ms):

   | total ms | calls | mean ms | statement |
   |---|---|---|---|
   | 112,061 | 159,922 | 0.70 | `WITH RECURSIVE project_hierarchy … WHERE id IN ($8)` — parent chain of one project, run for permission checks; 0.6× per request |
   | 94,188 + 93,268 + 66,485 | 18k + 30k + 12k | 3–5 | `WITH RECURSIVE all_projects …` — "all projects the user can access", three variants, ~61k executions for ~4.6k `GET /projects` calls: the same tree is recomputed several times per request and in other endpoints (`/tasks`, `/labels`, kanban) |
   | 93,004 + 82,340 (+ 3 more variants ≈ 130k) | 1,421 | **65 + 58** | `SELECT labels.* … WHERE label_tasks.task_id IN (SELECT id FROM tasks WHERE project_id IN (<every accessible project>))` plus a separate `count(DISTINCT labels.id)` with the identical WHERE — this is `GET /labels`. 20 ms at 1500 users, 65 ms at 3000. Cloud shows 271 ms p50 for it. |
   | 30,069 + 28,822 + 27,669 + 27,606 | ~2k | 52–72 | `SELECT DISTINCT tasks.* FROM tasks WHERE project_id IN (…) AND done=$2 … ORDER BY due_date, id LIMIT` — the home overview. `DISTINCT` on `tasks.*` forces a sort/unique of the whole candidate set before `LIMIT`. |
   | 5,130 | 310,600 | 0.02 | single-task `SELECT … FROM tasks WHERE id=$1` — cheap, but 1.7 per request: N+1 reads. |

   Also `projects` gets 255k sequential scans (315M tuples) and `team_members` 242k seq scans with its indexes
   used 19 times: these come from the recursive CTEs joining `team_members`/`users_projects` on every node.
   Fine at 700 projects; grows with instance size.
4. `GET /projects`, `GET /labels`, `GET /user`, `GET /tasks [home]` are the slowest endpoints in every run and are
   exactly the "open the app" bundle — the cold-start experience degrades first.

## Recommendations — code

Ordered by expected impact.

1. **Compute "accessible projects" once per request and reuse it.** `all_projects` runs 3× per `/projects`
   call and again inside `/tasks`, `/labels`, kanban. Memoize per request (context value), or better: maintain a
   `user_project_access` materialised table / closure table updated on share/move events, so permission checks
   become an indexed lookup instead of a recursive CTE. This also removes most `project_hierarchy` calls
   (160k per 10 min).
2. **Rewrite `GET /labels`.** Replace `task_id IN (SELECT id FROM tasks WHERE project_id IN (…))` with a join
   `label_tasks → tasks → accessible projects` (or `EXISTS`), drop the duplicate `count(DISTINCT …)` query when
   the page isn't full, and consider a `labels(created_by_id)` index. 65 ms → low single digits.
3. **Home overview (`/tasks`)**: drop `DISTINCT` (dedupe in Go if needed, or `DISTINCT ON (id)`), add a composite
   index `(done, due_date, id)` or `(project_id, done, due_date)` so the `ORDER BY … LIMIT` can walk an index.
4. **Cut statements per request (15 → <5)**: batch the per-task lookups (`SELECT … WHERE id=$1` 1.7× per request,
   `labels … WHERE task_id IN` once per task list), load task details with joins. Each round-trip is only
   0.1 ms of DB time but ~0.5-1 ms of latency in Go + network, and it's the majority of request time when the DB
   is idle (500-user run: 1 ms DB vs 18 ms request).
5. **Saved-filter listener** (`runs/seed-2026-08-29/findings.md` #1): O(saved filters) queries per task write.
   Not visible in these read-heavy runs but it pinned the DB during seeding; it will hurt on any write-heavy
   instance with many users.
6. **Login storm**: bcrypt cost is fine, but a login burst monopolises all cores because hashing runs inline in
   the request goroutines. A small semaphore (e.g. `runtime.NumCPU()` concurrent bcrypt) keeps the rest of the
   API responsive during storms. Refresh tokens already avoid re-login (v2 refresh cookie fixed in go-vikunja/vikunja#3651).
7. The 3× HTTP 500 on `POST /projects/{id}/tasks` under overload should be looked at in the Vikunja log
   (probably a timeout/`pq: canceling statement` surfacing as 500).

## Recommendations — hosting

1. **Postgres is the first thing to scale.** On 4/4 cores the practical ceiling for this traffic mix is
   ~2500 simulated users / ~500 rps. Give the DB 8 dedicated cores (ccx33) before touching the app box; Vikunja
   itself was at 60 %.
2. **Lower the connection pool.** `database.maxopenconnections=100` against a 4-core Postgres is
   counter-productive: 100 active backends on 4 cores is what produced load 49 and 4× slower statements.
   Set it to ~2-3× DB cores (8-12) and let Go queue; latency under overload gets better, not worse. Re-run the
   3000-user test with that single change — expect p95 to drop substantially. PgBouncer in transaction mode is
   the equivalent for multi-instance setups.
3. Vikunja is stateless enough to run 2+ replicas behind the existing proxy if the app box ever becomes the
   limit; it is not the limit today.
4. Keep `pg_stat_statements` + this dashboard on production; the top-statement table pointed at every problem
   within minutes.

## Context vs. real load

Vikunja Cloud's log averaged ~3 rps over two weeks (peaks in the tens). A single ccx23 pair serves >100× that,
so today's problems on Cloud are latency of specific endpoints (`/labels`, `/projects`, `/tasks` overview —
the same ones as here) on larger per-user datasets, not throughput. The big-workspace scenario (few users, many
projects/tasks/labels) is the next run to do; the recursive CTEs and the labels query scale with data size, not
with user count.

## Test-side notes

- Locust took 17 min to shut down after the 3000-user run (one user stuck in a request with a 60 s timeout
  loop); results are complete, just `end` is late. Worth adding `--stop-timeout 30` to `run.sh`.
- Whole-run p95/p99 in `findings.md` include the ramp-up spike; use the steady-state columns above to compare
  runs. Spawn rate 25/s is itself a login-storm test.
