---
name: analyze-runs
description: Analyze and compare load-test runs under runs/ (locust csv, pg_stat_statements dumps, Grafana/Prometheus, Vikunja logs) and write a capacity report with code + hosting recommendations. Use when asked to "compare runs", "analyze today's runs", "write a report", "check the top queries", or "check vikunja logs for errors" after run-test.sh.
---

# Analyze runs

Everything below runs from `testing-v2/`. Infra must still be up for the Prometheus / DB / log parts; the
locust csv + pg dumps in `runs/` work offline.

## 0. Inputs

- IPs + secrets: `infra/.env` (`DB_IP`, `VIKUNJA_IP`, `MONITORING_IP`, `LOADGEN_IP` public; `*_PIP` private 10.0.1.x).
- Per run `runs/<name>/<ts>/`: `meta.txt` (users, spawn rate, `from`/`to` in ms, vikunja version), `findings.md`
  (pre-filled summary + failures list), `locust_stats.csv` (per endpoint), `locust_stats_history.csv` (per ~1 s),
  `pg-top-statements.txt` (psql -x), `pg-totals.txt`, `pg-seq-scans.txt`, `grafana/*.png`.
- Previous report for comparison: `runs/report-<date>-capacity.md`. Compare against the last one, same user counts.
- Vikunja source for tracing queries/log lines: `~/www/projects/vikunja/vikunja/main` (git; version in `meta.txt`
  is `git describe`, e.g. `v2.5.0-345-g5694ef63` → commit `5694ef63`). `git log --oneline <old>..<new>` shows what
  changed between two reports.

## 1. Locust numbers (offline)

```bash
python3 .claude/skills/analyze-runs/scripts/locust_summary.py runs/baseline/<ts1> runs/baseline/<ts2> ...
```

Prints per-endpoint table across runs, steady-state vs ramp p50/p95/p99, the unix window of the steady state
(use it for Prometheus), and a timeline of the last run. Rules:

- **Whole-run p95/p99 in `findings.md` are dominated by the ramp** (25 logins/s = bcrypt storm). Always report
  steady state (second half of the full-load window) separately from the ramp.
- `User Count` below target for the whole run = spawn stalled; users < target at the end = users died (login
  retries exhausted, shows as `exception: the JSON object must be str...` in failures).
- Failure taxonomy: `OSError(99, 'Cannot assign requested address')` = loadgen ephemeral port exhaustion, not
  Vikunja. `RetriesExceeded(... timed out)` = 60 s client timeout. Only `HTTPError 5xx` counts against Vikunja.

## 2. Postgres statements (offline)

```bash
python3 .claude/skills/analyze-runs/scripts/pgsum.py runs/baseline/*/pg-top-statements.txt
cat runs/baseline/<ts>/pg-totals.txt      # statements, exec ms, plan ms, index usage of top seq-scan tables
cat runs/baseline/<ts>/pg-seq-scans.txt
```

Look for: share of total time per statement, mean ms growth between user counts (contention: same query,
higher mean, 100 % cache hit = CPU/queueing, not IO), calls per request (`calls / locust requests`), single-row
lookups with >1 call per request (N+1), `shared_blks_hit / calls` (buffers per call; >1000 for a small result
means a bad plan). Query text in the dump is cut at 400 chars; get the full text from the live DB.

## 3. Live DB: full query text, EXPLAIN, settings

Write SQL to a file and pipe it; inline quoting through ssh breaks. Host key changes on every `setup.sh`, so:

```bash
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
$SSH root@$DB_IP 'docker exec -i perf-postgres-1 psql -U vikunja -d vikunja -X' < q.sql
```

Useful `q.sql` pieces:

```sql
\x off
select calls, round(mean_exec_time::numeric,2) mean_ms, round(mean_plan_time::numeric,2) plan_ms, query
  from pg_stat_statements where query like '%due_date%LIMIT%' order by total_exec_time desc limit 3;
-- accessible project ids of a user, then EXPLAIN a real query with them
select string_agg(id::text, ',') from projects where owner_id = 5 \gset
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) SELECT tasks.* FROM tasks WHERE project_id IN (:string_agg) AND done = false
  AND (deleted_at = '0001-01-01' OR deleted_at IS NULL) ORDER BY due_date ASC NULLS LAST, id DESC NULLS LAST LIMIT 50;
select tablename, indexdef from pg_indexes where tablename in ('tasks','projects') order by 1;
show pg_stat_statements.track_planning; show jit; show shared_buffers;
```

Do EXPLAIN for a light user (few projects) *and* a heavy one (team-shared projects; find via
`team_members join team_projects`) — plans flip between them. The grants CTE lives in
`pkg/models/project_access.go`; copy it verbatim with a literal user id.

## 4. Prometheus (host / container / backends)

Prometheus binds to the private IP, not localhost. Copy the script over and run it there with the steady-state
windows from step 1 (or `from`/`to` from `meta.txt` divided by 1000; drop the first ~2 min for the ramp):

```bash
scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null .claude/skills/analyze-runs/scripts/prom.py root@$MONITORING_IP:/tmp/
$SSH root@$MONITORING_IP 'python3 /tmp/prom.py 500 <start> <end> 1500 <start> <end> 3000 <start> <end>'
```

For a timeline of one series (e.g. idle-in-transaction vs rps during the ramp):

```bash
curl -s -G http://10.0.1.3:9090/api/v1/query_range --data-urlencode 'query=pg_stat_activity_count{datname="vikunja",state="idle in transaction"}' \
  --data-urlencode start=<s> --data-urlencode end=<e> --data-urlencode step=30
```

Read it as: `load1 >> active backends` = connection contention (pool too big); `idle in transaction` high =
connections held across Go work (every `db.NewSession()` does `Begin()`); host CPU max ~100 % on the Vikunja box
during the ramp = bcrypt; loadgen `TCP_tw` near 24k = port exhaustion (range 32768–60999).
Known dashboard bug: `sum(locust_requests_current_rps)` double counts (includes the `Aggregated` row); trust the csv.

## 5. Vikunja logs

`VIKUNJA_LOG_HTTP=off` and level WARNING on the test host, so only errors/panics appear:

```bash
$SSH root@$VIKUNJA_IP 'docker logs --since <ISO from meta from/1000> perf-vikunja-1 2>&1 > /tmp/v.log;
  grep -v level=INFO /tmp/v.log | sed -E "s/time=[^ ]+ //; s/[0-9]{3,}/N/g" | sort | uniq -c | sort -rn | head;
  grep "<msg>" /tmp/v.log | cut -c6-21 | sort | uniq -c'   # per-minute histogram
```

Trace a message to source with `grep -rn "<msg>" --include='*.go' pkg` in the Vikunja checkout, then find who
logs it (`log.Error(err)` callers). Known: `user in context is not jwt token` = metrics middleware
(`pkg/routes/metrics.go`) on unauthenticated routes, harmless spam. `docker inspect --format '{{json .State.Health}}'`
— the compose healthcheck uses `wget`, missing from the image, so `unhealthy` is expected noise.

## 6. Report

Write `runs/report-<date>-capacity.md` following `runs/report-2026-08-30-capacity.md`: runs + versions + what
changed since the last report; numbers table (steady state, previous values in parentheses); "what happened"
(ramp vs steady, which box is the wall, failure taxonomy, top statements with EXPLAIN evidence); code
recommendations ordered by impact with file:line; hosting recommendations; test-side notes. Append 3–5 bullet
observations to each run's `findings.md` (replace the empty `- ` under Observations). Commit both:
`docs: capacity report for <date> runs (...)`.

## Gotchas

- Pool is `VIKUNJA_DATABASE_MAXOPENCONNECTIONS=100` in `infra/hosts/vikunja/compose.yaml`; Postgres config in
  `infra/hosts/db/postgresql.conf` (mounted, `pg_reload_conf()` after scp to `/opt/perf/`; exporter queries in
  `exporter-queries.yaml`, `docker compose restart postgres-exporter`).
- `pg_stat_statements` is reset at run start, so dumps are per run; `mean_plan_time` is 0 in runs before
  `track_planning` was enabled (2026-08-30).
- zsh: don't put ssh options in a `$VAR` and expand unquoted — word splitting breaks `-o`.
- `known_hosts` entries go stale on every `setup.sh`; always pass `UserKnownHostsFile=/dev/null`.
