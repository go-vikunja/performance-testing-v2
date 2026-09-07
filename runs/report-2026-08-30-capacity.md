# Capacity report: 500 / 1500 / 3000 concurrent users (2026-08-30)

Runs: `2026-08-30_17-56-32-baseline` (500), `2026-08-30_18-12-01-baseline` (1500), `2026-08-30_18-26-40-baseline` (3000).
Same seed as yesterday (100 accounts, 1293 projects, 51k tasks, 600 labels), classes `Worker Glancer IntegrationBot`,
10 min each, spawn rate 25/s for all three. Vikunja `v2.5.0-345-g5694ef63` (yesterday: `-249`), Postgres 18,
ccx23 + ccx23, pool still `maxopenconnections=100`.

What changed in Vikunja between the two reports: per-request access memo + one `grants` CTE for project permissions
(`b6d9e9c9c`, `b2e8cc991`, `943eac308`), labels listing without the `label_tasks` join (`5db6b0f4b`), `DISTINCT` only
when a join can multiply rows (`cccb76e80`), composite index `(done, due_date)` (`a8d4a2b4b`), v2 refresh cookie fix.
Yesterday's numbers in parentheses where they differ.

## Numbers

Steady state = second half of the full-load window from `locust_stats_history.csv`; host/container numbers are
Prometheus averages over the same window.

| | 500 users | 1500 users | 3000 users |
|---|---|---|---|
| requests / whole-run rps | 63,993 / 104 | 177,638 / 288 | 271,067 / 439 |
| steady-state rps | 106 | 316 (310) | ~550 (510) |
| steady p50 / p95 / p99 ms | 19 / 31 / 55 (17 / 37 / 320) | 14 / 28 / 52 (13 / 28 / 50) | 140 / 1,500 / 2,000 (200 / 1,900 / 2,500) |
| ramp-up p50 / p95 ms | 29 / 58 | 1,600 / 5,000 (3,300 / 13,000) | 6,000–9,800 / 27,000–45,000 (6,900 / 26,000) |
| failures | 0 | 0 | 345, none HTTP 5xx (see below) |
| DB host CPU avg / max | 23 % / 31 % (28 / 30) | 42 % / 50 % (45 / 63) | 62 % / 73 % (78 / 95) |
| Postgres container cores avg / max | 0.78 / 0.98 | 1.52 / 1.74 | 2.37 / 2.72 (3.03) |
| DB load1 avg / max | 0.9 / 2.7 | 3.3 / 12 | 21 / 32 (35 / 49) |
| Vikunja host CPU avg / max | 27 % / 58 % | 43 % / 97 % | 58 % / **99.7 %** |
| Vikunja container cores avg / max | 0.89 / 2.17 | 1.52 / 3.70 | 2.12 / 3.93 |
| Vikunja RSS max / goroutines avg (max) | 209 MB / 1.1k (1.6k) | 316 MB / 2.9k (4.2k) | 460 MB / 5.4k (7.8k) |
| Postgres backends active avg / max | 0.8 / 2 | 1.0 / 4 | 2.5 / 25 |
| Postgres backends **idle in transaction** avg / max | 1.7 / **87** | 1.5 / 10 | 9.8 / **94** |
| DB exec time ms per second avg / max | 131 / 307 (147) | 283 / 617 (418) | 1,194 / 1,586 (2,541) |
| statements per request | 13.1 (15) | 12.9 (14.9) | 12.6 (14.7) |
| avg ms per statement | 0.106 | 0.10 | 0.19 (0.38) |
| DB exec ms per request | 1.4 | 1.0 (1.6) | 2.4 (5.6) |
| cache hit / block IO / lock waits | 100 % / 0 / 0 | 100 % / 0 / 0 | 100 % / 0 / 0 |
| loadgen TCP sockets alloc / TIME_WAIT max | 0.9k / 0.5k | 2.5k / 9.4k | 4.3k / **24k** |

Note: `pg_stat_statements.track_planning` is off, so "DB exec time" excludes planning. Measured by hand, planning is
0.6–1.0 ms per statement here (see code #4), i.e. comparable to execution.

## What happened

1. **The perf commits halved DB work.** At 3000 users DB exec time per request went 5.6 → 2.4 ms, Postgres
   container CPU 3.0 → 2.4 cores, load1 49 → 32, statements per request 14.7 → 12.6. Steady-state latency at 3000
   improved (p50 200 → 140 ms, p95 1.9 → 1.5 s) at slightly higher throughput. 500 and 1500 are unchanged: they were
   never DB-bound; p99 at 500 is much better (320 → 55 ms) because the 500 run used spawn rate 25 today and the
   whole-run p99 is dominated by the ramp.
2. **The login storm is the worst part of every run, and it's a pool problem, not (only) a CPU problem.** During
   the 3000-user ramp (0–140 s) rps sat at ~125 while p50 climbed to 9.8 s and p95 to 45 s; steady state afterwards
   was ~550 rps at p50 140 ms. Prometheus shows 64–84 backends *idle in transaction* for the whole ramp (and 87 at
   500 users, where the DB was otherwise idle). `db.NewSession()` always does `Begin()`, so every request holds a
   pooled connection in an open transaction for its whole lifetime, including bcrypt in `CheckUserCredentials`
   (`pkg/user/user.go:144` opens the session, then hashes). 25 logins/s × bcrypt at 100 %-CPU pace = the 100-connection
   pool is full of idle logins, and every other request queues for a connection. Same pattern shows up as short
   spikes (43 and 83 idle-in-tx) at 420 s and 570 s in steady state, which coincide with the only failure bursts.
3. **At 3000 users the two boxes are now equally loaded** (DB 62 % avg, Vikunja 58 % avg, both peak >70 %). Yesterday
   the DB was clearly the wall; today the wall has moved to "both", with the Vikunja host pinned at 100 % in bursts
   (bcrypt). Postgres load1 21–32 on 4 cores with only 2.5 *active* backends on average means the queueing is from
   ~100 connections context-switching, not from actual work.
4. **The 345 failures at 3000 users were all on the load generator or timeouts, zero HTTP 5xx.** 249× `OSError(99,
   'Cannot assign requested address')` = ephemeral port exhaustion on loadgen (port range 32768–60999 = 28k ports,
   TIME_WAIT peaked at 24k + 4.3k open; `tcp_tw_reuse=2` only applies to loopback). ~80× `RetriesExceeded … timed out`
   (60 s client timeout during the ramp), 17× locust exceptions (users whose login returned no body after retries).
   The Vikunja log for the window has no 5xx, no panics, no DB errors. It does have 31,186 lines of
   `level=ERROR msg="user in context is not jwt token"` — see code #6. `VIKUNJA_LOG_HTTP=off`, so 5xx would only be
   visible via locust, which reported none. (Yesterday's 3× 500 on task create did not reproduce.)
5. **Top statements** (3000 run, `pg-top-statements.txt`; share of total DB exec time):

   | share | total ms | calls | mean ms | statement |
   |---|---|---|---|---|
   | 48 % | 256,932 | 202,779 | 1.27 (0.58 at 1500) | `WITH RECURSIVE grants … tree …` — the new per-request access resolution, 0.75× per request. Replaced yesterday's `all_projects`/`project_hierarchy` family (which was ~50 % too, of twice the total). |
   | 12.6 % + ~9 % in variants | 67,057 | 2,290 | **29** (7.5 at 1500, 9 at 500) | `SELECT tasks.* … WHERE project_id IN (…) AND done=false … ORDER BY due_date ASC NULLS LAST, id DESC LIMIT` — home overview. |
   | 2.9 % | 15,345 | 101,331 | 0.15 | `WITH RECURSIVE project_hierarchy … WHERE t.id IN ($6)` — parent chain per task read (bots' `GET /tasks/{id}`), 0.37× per request. |
   | 2.8 % | 14,689 | 2,129 | 6.9 (2.9 at 1500) | `SELECT labels.* … WHERE labels.id IN (SELECT … label_tasks JOIN tasks … project_id IN (…)) OR created_by_id IN (…)` — `GET /labels`, was 65 ms yesterday. |
   | 2.6 % | 14,028 | 61,557 | 0.23 | `SELECT labels.*, label_tasks.task_id … WHERE task_id IN (…)` — labels per task list. |
   | 1.6 % + 1.0 % + 0.8 % | 18.5k | 211k + 313k + 232k | 0.02–0.04 | single-row `tasks`/`projects`/`users` by id — 2.8 per request. |

   `EXPLAIN (ANALYZE, BUFFERS)` on the live DB, not under load:

   - **grants CTE, user 5 (8 projects): 1.6 ms exec + 0.9 ms planning, 332 buffers, of which 294 are the recursive
     step**: the planner merge-joins `projects` against the work table by doing a full scan of
     `IDX_projects_parent_project_id` (1,251 rows per iteration). The reason the scan is that long: 1,193 of 1,293
     projects have `parent_project_id = 0`, not `NULL`, so every root project is in the index and gets scanned on every
     recursion level. The actual answer is 10 rows.
   - **home overview, user 19 (28 accessible projects): 6.1 ms, 3,804 buffers**: the planner now uses the new
     `IDX_tasks_done_due_date` index, walks it in `due_date` order and filters by `project_id IN (…)`, discarding 3,699
     rows to find 50. For a user with 8 projects it uses `IDX_tasks_project_id` instead: 1.1 ms, 102 buffers. Under
     contention the 28-project variant is the 29 ms one. The composite index made the small case fine and the big
     case worse.
   - **labels, user 19: 2.6 ms, 1,989 buffers**: nested loop over 730 tasks → `label_tasks` index probes. Fine now;
     scales with task count, not label count.
6. `GET /projects`, `GET /user`, `GET /labels`, `GET /tasks [home]`, `POST /login` are again the slowest endpoints in
   every run — the "open the app" bundle — but their p50s are all ≤ 1.6 s at 3000 users now (vs 2.9 s+ yesterday)
   and their whole-run averages are inflated by the ramp. In steady state at 1500 users all of them are < 50 ms p95.

## Recommendations — code

Ordered by expected impact.

1. **Stop holding a transaction (and a pooled connection) for the whole request.** `db.NewSession()` `Begin()`s
   unconditionally, so a `GET` holds one of 100 connections idle-in-transaction while Go serialises JSON, while
   bcrypt runs, while the websocket handshake happens. Options, in order of preference: (a) read-only handlers use a
   session without `Begin()` (xorm autocommit) and only writes open a transaction; (b) at minimum, run
   `CheckUserCredentials`/bcrypt *before* opening the session in login and token refresh; (c) lazily begin on the first
   write. This is what turns 25 logins/s into a 100-connection pile-up and is the single biggest lever for the ramp
   and for pool sizing (hosting #1). It also removes the `BEGIN`/`COMMIT` round trips from every read.
2. **Make the grants CTE cheap.** (a) Store `NULL` instead of `0` in `projects.parent_project_id` for root projects
   (migration + model default) and add a partial index `ON projects (parent_project_id) WHERE parent_project_id IS NOT
   NULL` — the recursive step's index scan then covers only real child projects (100 rows here instead of 1,293) and
   buffers drop ~10×. (b) Cache the resolved access map per user across requests (short TTL or invalidate on
   project/share/team writes), not only per session: bots pay 1.3 ms + 0.9 ms planning on every `GET /tasks/{id}`.
   (c) `project_hierarchy` per task read (101k calls) can be answered from the same memo.
3. **Home overview index.** Replace `IDX_tasks_done_due_date (done, due_date)` with `(project_id, done, due_date)`
   (or keep both and check the planner's choice with a 30-project user). The `project_id IN (…)` predicate is the
   selective one; `done` alone is not. Expect 3,800 → ~300 buffers for the heavy case, 29 ms → ~2 ms under load.
4. **Turn on `pg_stat_statements.track_planning` and look at planning time; then consider pgx.** Vikunja uses
   `lib/pq`, which sends every query as an unnamed prepared statement, so Postgres plans each of the 12.6 statements
   per request from scratch (0.6–1.0 ms each measured above, i.e. ~8–10 ms of DB CPU per request that the dashboard
   doesn't show and that is a large part of the 2.4 "active" cores). `pgx` via `database/sql` with its statement
   cache reuses named prepared statements per connection; xorm supports it with the `pgx` driver name. Cheap to try,
   measurable with the existing dashboard once `track_planning` is on.
5. **N+1 single-row reads**: `tasks`/`projects`/`users` by id = 2.8 statements per request (756k of 3.4M
   statements). Not expensive in exec time but each is a round trip + planning. Batch them (the access memo already
   has the project rows; the task list already has the task rows).
6. **Metrics middleware logs an ERROR for every unauthenticated request** (`pkg/routes/metrics.go:64`,
   `updateActiveUsersFromContext` → `GetAuthFromClaims` fails on `/login`, `/user/token/refresh`, `/info`, `/ws`).
   31k log lines in 10 minutes at 3000 users; at log level WARNING this is the *only* thing in the log, which hides
   real errors. Skip the update when there is no JWT in context instead of logging.
7. **Login storm CPU**: still worth a bcrypt semaphore (`runtime.NumCPU()` concurrent hashes) so a burst of logins
   can't pin the app host at 100 % and stall every other request; with #1 done the DB side of the problem is gone but
   the CPU side remains (Vikunja host max 99.7 % in every run today).
8. Compose healthcheck for the Vikunja container uses `wget`, which the image doesn't ship — the container has been
   reporting `unhealthy` the whole time (test-infra bug, but the same healthcheck is what people copy from docs).

## Recommendations — hosting

1. **Lower the pool now, and again after code #1.** `maxopenconnections=100` against 4 DB cores is still what
   produces load1 32 with 2.5 active backends. With today's code, 100 connections are needed only because each one
   is held idle-in-transaction for a whole request; after code #1 a pool of 2–3× DB cores (8–12) will serve the same
   load with less contention. Until then, ~32 is a reasonable compromise: it caps the pile-up and lets Go queue
   instead of Postgres. Either way, re-run the 3000-user test with the changed value only.
2. **Both boxes are at ~60 % average / >95 % peak at 3000 users; the next size up needs both.** The DB is no
   longer the sole wall. For >3000 simulated users on this traffic mix: DB to 8 dedicated cores (ccx33) *and* a second
   Vikunja replica (or ccx33) — Vikunja is CPU-bound on bcrypt + JSON, not memory (460 MB RSS at 3000 users).
3. `jit = on` (Postgres default) is wasteful for sub-millisecond OLTP statements; set `jit = off` on the DB host.
   Everything else in the Postgres config is fine for this box (4 GB shared_buffers, 100 % cache hit, no IO).
4. **Load generator**: set `net.ipv4.ip_local_port_range = 1024 65535` and `net.ipv4.tcp_tw_reuse = 1` in
   `infra/hosts/loadgen/post-deploy.sh` (or sysctl.d). Locust's `FastHttpUser` keeps connections alive, but 3000 users
   plus Glancer churn and websocket reconnects still cycled 24k sockets through TIME_WAIT; that, not Vikunja, is what
   failed 249 requests. Loadgen CPU was 22 % avg / 35 % max, so one locust process is still fine.
5. Ramp: 25 users/s is a login-storm test in itself. For capacity numbers use 10/s (or pre-warm sessions); keep one
   25/s run as the "everyone comes back after an outage" scenario, since that is exactly the case code #1 fixes.

## Test-side notes

- The dashboard's "Users - RPS" panel (`sum(locust_requests_current_rps)`) reports ~1,100 rps at 3000 users while
  locust's own csv says ~550; the exporter's `Aggregated` row is being summed together with the per-endpoint rows.
  Filter it out in `gen_dashboard.py`.
- Whole-run p95/p99 in `findings.md` still include the ramp; use the steady-state row above to compare runs.
- Locust shut down cleanly this time (`--stop-timeout 30` works); 31 of 3000 users died during the ramp (login
  retries exhausted) — the `2969` user count in the history csv is that.
