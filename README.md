# Vikunja performance testing (v2 API)

Load tests for Vikunja's `/api/v2` on Hetzner Cloud, with Postgres instrumented so Grafana shows
whether time goes into the database or into Vikunja itself, and how reads and writes split.

## Layout

```
infra/            hcloud provisioning + per-host docker compose files
  config.sh       server types, location, images (edit or override via env)
  setup.sh        create network, firewalls, 4 servers; deploy compose stacks
  teardown.sh     delete everything (--purge also drops infra/.env secrets)
  reset.sh        wipe DB volume, restart vikunja, reseed, reset pg stats
  run-test.sh     one headless locust run + archive locust html/csv + grafana pngs
  hosts/<role>/   compose.yaml + configs copied to /opt/perf on each host
locust/           seed script, locust user classes, run helper (runs on loadgen VM)
results/          created by run-test.sh (gitignored)
```

Servers (all Debian 13, everything in docker, private network `10.0.0.0/16`):

| role       | default type | runs                                                    |
|------------|--------------|---------------------------------------------------------|
| db         | ccx23        | postgres:18 (+pg_stat_statements), postgres-exporter, node-exporter, cadvisor |
| vikunja    | ccx23        | vikunja/vikunja:unstable, node-exporter, cadvisor       |
| monitoring | cx23         | prometheus, grafana (+image renderer), node-exporter    |
| loadgen    | cx33         | locust (on demand), locust-exporter, node-exporter      |

Firewall: only Grafana `:3000` is public. SSH `:22` is allowed from `ADMIN_IP` (your current IP at setup time)
only. Vikunja and Postgres are reachable on the private network only.

## Usage

```bash
hcloud context create vikunja-performance-testing   # once, needs API token
cd infra
./setup.sh                      # ~5 min. Prints grafana url/password, ssh hints
./reset.sh --users 100 --tasks 80        # seed (also: wipe + reseed between runs)
./run-test.sh baseline -u 500 -r 10 -t 10m
./run-test.sh bots -u 100 -c "IntegrationBot"
./run-test.sh collab -u 200 -c "Worker Collaborator" -e "WEIGHT_COLLAB=2"
./teardown.sh
```

Interactive: `ssh -L 8089:localhost:8089 root@<loadgen ip>` then on the box
`cd /opt/perf/locust && ./run.sh ui Worker Glancer` and open http://localhost:8089.

Override sizes: `TYPE_DB=ccx33 LOCATION=fsn1 ./setup.sh`. Secrets and discovered IPs live in `infra/.env`.

Note: the pre-auth rate limiter (`/login`, `/register`, `/ws`; 10/min per IP, always on) is raised to
effectively unlimited in `hosts/vikunja/compose.yaml`, since all load comes from one IP.

## Scenarios

Derived from two weeks of Vikunja Cloud access logs (3.5M requests):

- 80 % of requests came from API integrations (node scripts, Home Assistant): `GET /tasks/{id}` 65 %,
  `GET /projects/{id}/tasks?per_page=20|50` 23 %, `GET /projects` 9 %, no think time.
- Interactive traffic (browser/desktop/mobile): notifications polling 26 % (now websocket), avatars 14 %,
  `/user` 10 %, token refresh 10 %, then project list views, kanban, task detail, home overview.
  Writes are ~3 % of interactive requests.
- Half of all sessions are ~5 requests long (open app, look, leave); the other half are long working sessions.
  Think time between actions: median ~10-15 s, long tail to minutes.
- Slowest endpoints in production: `/labels` (271 ms p50), `/tasks` overview (207 ms), `/projects` (149 ms).

User classes in `locust/locustfile.py` (weights via `WEIGHT_WORKER`, `WEIGHT_GLANCER`, `WEIGHT_BOT`, `WEIGHT_COLLAB`):

| class            | models                                                                      |
|------------------|-----------------------------------------------------------------------------|
| `Worker`         | long session: list/kanban/gantt views, task detail, edits, moves, comments, labels; websocket open; token refresh every 10 min |
| `Glancer`        | login, app load, home overview, short websocket, gone for minutes           |
| `IntegrationBot` | polling API client, ~1 req/s per user                                       |
| `Collaborator`   | team member commenting/assigning in the owner's shared project; owner receives `notification.created` pushes (latency reported as `WS push notification.created`) |

Scenarios:

1. **Baseline** – `Worker Glancer IntegrationBot`, default seed (100 users × 6 projects × 80 tasks).
2. **Big workspace** – same classes, fat seed: `./reset.sh --users 20 --projects 10 --tasks 1000`.
3. **Collaboration** – `Worker Collaborator` with `WEIGHT_COLLAB=3`; watch websocket push latency and the
   Postgres write share.

Request shapes (filters, sort, expand, per_page) are copied from what the frontend sends; see `locust/common.py`.

## Reading the Grafana "Perf overview" dashboard

- *Where does a request's time go?* – locust average response time vs. Postgres execution time per request
  (from `pg_stat_statements`). If the curves track, the DB dominates; the gap is Vikunja + network.
- *Postgres: read/write split* – statements/s and exec-time by kind (SELECT vs INSERT/UPDATE/DELETE),
  tuples returned vs. fetched (seq scans vs. index), block IO time, backends by wait event, locks.
- *Top statements* – per-query exec time and call rate; `pg_stat_statements` is reset by `reset.sh`.
- Community dashboards (node exporter full, postgres, cadvisor) are provisioned alongside.

`run-test.sh` archives `locust-report.html` (locust's own charts), the csv history, the full dashboard render
and one png per panel into `results/<name>/`, plus `meta.txt` with a Grafana deep link for the time range.
