#!/usr/bin/env python3
"""Generates dashboards/perf-overview.json. Edit here, re-run, commit both."""
import json

DS = {"type": "prometheus", "uid": "prometheus"}
panels, y = [], 0
pid = 0

def panel(title, targets, unit="short", kind="timeseries", w=8, h=8, stack=False, max_=None, desc="", extra=None):
    global pid, y
    pid += 1
    x = sum(p["gridPos"]["w"] for p in panels if p["gridPos"]["y"] == y) if panels else 0
    if x + w > 24:
        y += h; x = 0
    p = {
        "id": pid, "type": kind, "title": title, "description": desc, "datasource": DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": {"unit": unit, "custom": {"lineWidth": 1, "fillOpacity": 10 if not stack else 40,
                        "stacking": {"mode": "normal" if stack else "none"}}}, "overrides": []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
        "targets": [{"refId": chr(65 + i), "expr": e, "legendFormat": l, "datasource": DS, **(o or {})}
                    for i, (e, l, *rest) in enumerate(targets) for o in [rest[0] if rest else None]],
    }
    if max_ is not None: p["fieldConfig"]["defaults"]["max"] = max_; p["fieldConfig"]["defaults"]["min"] = 0
    if extra: p.update(extra)
    panels.append(p)

def row(title):
    global pid, y
    if panels: y += max(p["gridPos"]["h"] for p in panels if p["gridPos"]["y"] == y)
    pid += 1
    panels.append({"id": pid, "type": "row", "title": title, "collapsed": False, "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}})
    y += 1

R = "[30s]"
row("Load (locust)")
panel("Users / RPS", [("locust_users", "users"), ('sum(locust_requests_current_rps)', "rps"),
                      ('sum(locust_requests_current_fail_per_sec)', "fail/s")])
panel("Response time (aggregated)", [('locust_requests_current_response_time_percentile_50', "p50"),
      ('locust_requests_current_response_time_percentile_95', "p95"),
      ('sum(locust_requests_avg_response_time * locust_requests_current_rps) / sum(locust_requests_current_rps)', "avg (rps-weighted)")], unit="ms")
panel("Where does a request's time go?", [
      ('sum(locust_requests_avg_response_time * locust_requests_current_rps) / sum(locust_requests_current_rps)', "avg locust response time"),
      ('sum(rate(pg_stat_statements_kind_total_exec_time' + R + ')) / sum(locust_requests_current_rps)', "DB exec time per request")],
      unit="ms", desc="If DB time per request tracks response time, Postgres dominates. Gap = time in Vikunja (Go, permission checks, JSON) + network.")
panel("Avg response time by endpoint", [('topk(12, locust_requests_avg_response_time)', "{{method}} {{name}}")], unit="ms", w=12)
panel("RPS by endpoint", [('topk(12, rate(locust_requests_num_requests' + R + '))', "{{method}} {{name}}")], w=12, stack=True)

row("Hosts")
panel("CPU busy", [('1 - avg by(host)(rate(node_cpu_seconds_total{mode="idle"}' + R + '))', "{{host}}")], unit="percentunit", max_=1)
panel("Container CPU (cores)", [('sum by(name)(rate(container_cpu_usage_seconds_total{name=~".*(vikunja|postgres).*"}' + R + '))', "{{name}}")])
panel("Container memory", [('container_memory_working_set_bytes{name=~".*(vikunja|postgres).*"}', "{{name}}")], unit="bytes")
panel("Disk IO (db)", [('rate(node_disk_read_bytes_total{host="db",device=~"sd.*|nvme.*|vd.*"}' + R + ')', "read {{device}}"),
                       ('rate(node_disk_written_bytes_total{host="db",device=~"sd.*|nvme.*|vd.*"}' + R + ')', "write {{device}}")], unit="Bps")
panel("Network (vikunja host)", [('rate(node_network_receive_bytes_total{host="vikunja",device!="lo"}' + R + ')', "rx {{device}}"),
                                 ('rate(node_network_transmit_bytes_total{host="vikunja",device!="lo"}' + R + ')', "tx {{device}}")], unit="Bps")
panel("Vikunja Go runtime", [('go_goroutines{job="vikunja"}', "goroutines"), ('go_memstats_heap_inuse_bytes{job="vikunja"}', "heap bytes", {"hide": False})])

row("Postgres: read/write split")
panel("Statements/s by kind", [('sum by(kind)(rate(pg_stat_statements_kind_calls' + R + '))', "{{kind}}")], stack=True,
      desc="From pg_stat_statements: SELECT = read, INSERT/UPDATE/DELETE = write.")
panel("DB exec time by kind (ms per s = busy backends)", [('sum by(kind)(rate(pg_stat_statements_kind_total_exec_time' + R + '))', "{{kind}}")], stack=True, unit="ms",
      desc="1000 ms/s = one backend fully busy. Compare with 4 cores.")
panel("Tuples/s", [('rate(pg_stat_database_tup_returned{datname="vikunja"}' + R + ')', "returned (scanned)"),
                   ('rate(pg_stat_database_tup_fetched{datname="vikunja"}' + R + ')', "fetched (via index)"),
                   ('rate(pg_stat_database_tup_inserted{datname="vikunja"}' + R + ')', "inserted"),
                   ('rate(pg_stat_database_tup_updated{datname="vikunja"}' + R + ')', "updated"),
                   ('rate(pg_stat_database_tup_deleted{datname="vikunja"}' + R + ')', "deleted")],
      desc="returned >> fetched means sequential scans / missing indexes.")
panel("Transactions/s", [('rate(pg_stat_database_xact_commit{datname="vikunja"}' + R + ')', "commit"),
                         ('rate(pg_stat_database_xact_rollback{datname="vikunja"}' + R + ')', "rollback")])
panel("Cache hit ratio", [('rate(pg_stat_database_blks_hit{datname="vikunja"}' + R + ') / (rate(pg_stat_database_blks_hit{datname="vikunja"}' + R + ') + rate(pg_stat_database_blks_read{datname="vikunja"}' + R + '))', "hit ratio")], unit="percentunit", max_=1)
panel("Block IO time (ms/s)", [('rate(pg_stat_database_blk_read_time{datname="vikunja"}' + R + ')', "read"),
                               ('rate(pg_stat_database_blk_write_time{datname="vikunja"}' + R + ')', "write")], unit="ms")
panel("Backends by state / wait", [('sum by(state,wait_event_type)(pg_activity_count)', "{{state}} {{wait_event_type}}")], stack=True)
panel("Locks waiting / deadlocks", [('pg_locks_waiting_count', "waiting"), ('rate(pg_stat_database_deadlocks{datname="vikunja"}' + R + ')', "deadlocks/s")])
panel("Seq vs index scans", [('sum(rate(pg_stat_user_tables_seq_scan' + R + '))', "seq scan"),
                             ('sum(rate(pg_stat_user_tables_idx_scan' + R + '))', "idx scan")])

row("Postgres: top statements")
panel("Top queries by total exec time (ms/s)", [('topk(15, sum by(query)(rate(pg_stat_statements_top_total_exec_time[1m])))', "{{query}}")], unit="ms", w=24, h=10)
panel("Top queries (table, instant)", [
    ('topk(20, sum by(query)(rate(pg_stat_statements_top_total_exec_time[5m])))', "", {"instant": True, "format": "table"}),
    ('sum by(query)(rate(pg_stat_statements_top_calls[5m]))', "", {"instant": True, "format": "table"}),
    ('avg by(query)(pg_stat_statements_top_mean_exec_time)', "", {"instant": True, "format": "table"})],
    kind="table", w=24, h=12, extra={"transformations": [
        {"id": "merge"},
        {"id": "organize", "options": {"excludeByName": {"Time": True}, "renameByName": {"Value #A": "ms/s", "Value #B": "calls/s", "Value #C": "mean ms"}}},
        {"id": "sortBy", "options": {"sort": [{"field": "ms/s", "desc": True}]}}]})
panel("Table seq scans/s", [('topk(10, rate(pg_stat_user_tables_seq_scan[1m]))', "{{relname}}")], w=12)
panel("Table rows written/s", [('topk(10, rate(pg_stat_user_tables_n_tup_ins[1m]) + rate(pg_stat_user_tables_n_tup_upd[1m]) + rate(pg_stat_user_tables_n_tup_del[1m]))', "{{relname}}")], w=12)

row("Vikunja")
panel("Entities", [("vikunja_active_users", "active users"), ("vikunja_task_count", "tasks"), ("vikunja_project_count", "projects")])

dash = {"uid": "perf-overview", "title": "Perf overview", "schemaVersion": 39, "editable": True, "refresh": "5s",
        "time": {"from": "now-15m", "to": "now"}, "timezone": "browser", "panels": panels, "templating": {"list": []}}
json.dump(dash, open("dashboards/perf-overview.json", "w"), indent=1)
print(len(panels), "panels")
