# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Load tests for Vikunja's `/api/v2` on Hetzner Cloud. Four VMs (db, vikunja, monitoring, loadgen), everything in docker, Postgres instrumented with `pg_stat_statements` so Grafana shows DB vs. Vikunja time and read/write split. See `README.md` for the scenario rationale (derived from Vikunja Cloud access logs) and how to read the dashboard. Each run folder under `runs/<name>/<timestamp>/` has a `findings.md`; `runs/seed-2026-08-29/findings.md` holds the bugs found while seeding.

No unit tests, no linter. The only "test" is a real run against the infra.

## Commands

All `infra/*.sh` scripts are `nix-shell` shebangs (hcloud, ssh, envsubst, python3 from nixpkgs) and must be run from `infra/`. They source `config.sh` (tunables, override via env: `TYPE_DB=ccx33 LOCATION=fsn1 ./setup.sh`) and `infra/.env` (generated secrets + discovered IPs, gitignored; `*_IP` is public, `*_PIP` private).

```bash
hcloud context create vikunja-performance-testing   # once
cd infra
./setup.sh                                  # provision + deploy, ~5 min
./reset.sh --users 100 --tasks 80           # wipe DB volume, restart vikunja, reseed, reset pg stats. Args go to seed.py
./run-test.sh NAME -u 500 -r 10 -t 10m -c "Worker Glancer IntegrationBot" -e "WEIGHT_BOT=2"
./teardown.sh [--purge]                     # --purge also drops infra/.env
```

`run-test.sh` and `reset.sh` both `scp` `locust/` to the loadgen VM and rebuild the `perf-locust` image before running, so local edits to `locust/` are picked up automatically; no separate deploy step. Results land in `runs/NAME/<timestamp>/` (committed; png/html via git-lfs): locust html/csv, `grafana/*.png` per panel, `pg-top-statements.txt`, `pg-seq-scans.txt`, `meta.txt` with Grafana deep link and Vikunja version, and a pre-filled `findings.md` to add observations to.

On the loadgen VM (`ssh root@$LOADGEN_IP`, `cd /opt/perf/locust`): `./run.sh seed|ui|headless`. Interactive UI: `ssh -L 8089:localhost:8089`, then `./run.sh ui Worker Glancer`.

Grafana dashboard: edit `infra/hosts/monitoring/grafana/gen_dashboard.py`, re-run it, commit both it and the generated `dashboards/perf-overview.json`. Do not hand-edit the JSON.

## Architecture

- `infra/hosts/<role>/` — compose.yaml + configs, copied to `/opt/perf` on each host by `setup.sh`; `post-deploy.sh` there runs on the host after copy (loadgen's writes `locust/.env` with `VIKUNJA_PIP`, `MONITORING_PIP`, `GRAFANA_PASSWORD`).
- `locust/seed.py` — creates users/projects/tasks/labels/teams via the API and writes `seed-state.json` (accounts, projects, task ids). `--from-existing` rebuilds the state file from an already seeded instance without seeding. All seeded accounts share `PASSWORD` from `common.py`.
- `locust/locustfile.py` — `VikunjaUser` base (login, token refresh every 5 min because JWTs live 10 min, websocket via `ws_client.py`) and four concrete classes: `Worker`, `Glancer`, `IntegrationBot`, `Collaborator`. Class selection is by positional args to locust; weights via `WEIGHT_<NAME>` env vars, which `run.sh` forwards into the container.
- `locust/common.py` — request shapes (filter/sort/expand/per_page) copied from what the real frontend sends. Change these only when the frontend changes; they are what makes the load realistic.
- `locust/ws_client.py` — minimal Vikunja websocket client; reports connect and push latency as locust `WS` requests (e.g. `WS push notification.created`).
- Rate limiter on `/login` etc. is raised to unlimited in `hosts/vikunja/compose.yaml` since all load comes from one IP.

## Gotchas

- Seeding 100 users × 48k tasks is slow because of a Vikunja bug (findings #1); Postgres pins its cores. Not a seed script problem.
- `pg_stat_statements` is only reset by `reset.sh`; a `run-test.sh` without a preceding reset shows cumulative stats.
- Headless runs keep locust's web UI up (`--autostart`) so `locust-exporter` can scrape it; `run.sh` kills leftover containers and waits for `:8089` before starting.
- Locust users skip projects with no tasks (the default Inbox); seed enough tasks or user classes will have nothing to hit.

