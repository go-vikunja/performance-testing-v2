#!/usr/bin/env python3
"""Host/container/postgres metrics per time window. Runs ON the monitoring host (prometheus binds MONITORING_PIP:9090).
Usage: prom.py <label> <start_unix> <end_unix> [<label> <start> <end> ...]"""
import json, sys, urllib.parse, urllib.request

PROM = "http://10.0.1.3:9090"


def q(expr, t):
    u = PROM + "/api/v1/query?" + urllib.parse.urlencode({"query": expr, "time": t})
    r = json.load(urllib.request.urlopen(u))["data"]["result"]
    out = []
    for x in r:
        m = x["metric"]
        k = m.get("host") or m.get("name") or m.get("state") or ""
        out.append(f"{k}={float(x['value'][1]):.2f}")
    return " ".join(out) or "n/a"


a = sys.argv[1:]
for label, s, e in zip(a[::3], a[1::3], a[2::3]):
    s, e = int(s), int(e)
    d = e - s
    R = f"[{d}s:15s]"
    print(f"=== {label}: window {d}s ({s}..{e})")
    print(" host cpu busy% avg:", q(f"100*(1-avg by(host)(avg_over_time(rate(node_cpu_seconds_total{{mode='idle'}}[1m]){R})))", e))
    print(" host cpu busy% max:", q(f"100*(1-min by(host)(min_over_time(rate(node_cpu_seconds_total{{mode='idle'}}[1m]){R})))", e))
    print(" load1 avg:", q(f"avg by(host)(avg_over_time(node_load1[{d}s]))", e), "| max:", q(f"max by(host)(max_over_time(node_load1[{d}s]))", e))
    print(" container cores avg:", q(f"avg by(name)(avg_over_time(rate(container_cpu_usage_seconds_total{{name=~'perf-(vikunja|postgres)-1'}}[1m]){R}))", e))
    print(" container cores max:", q(f"max by(name)(max_over_time(rate(container_cpu_usage_seconds_total{{name=~'perf-(vikunja|postgres)-1'}}[1m]){R}))", e))
    print(" container mem MB max:", q(f"max by(name)(max_over_time(container_memory_working_set_bytes{{name=~'perf-(vikunja|postgres)-1'}}[{d}s]))/1e6", e))
    print(" goroutines avg:", q(f"avg_over_time(go_goroutines{{job='vikunja'}}[{d}s])", e), "max:", q(f"max_over_time(go_goroutines{{job='vikunja'}}[{d}s])", e))
    print(" vikunja RSS MB max:", q(f"max_over_time(process_resident_memory_bytes{{job='vikunja'}}[{d}s])/1e6", e))
    print(" vikunja open fds max:", q(f"max_over_time(process_open_fds{{job='vikunja'}}[{d}s])", e))
    print(" pg backends avg:", q(f"avg by(state)(avg_over_time(pg_stat_activity_count{{datname='vikunja',state=~'active|idle|idle in transaction'}}[{d}s]))", e))
    print(" pg backends max:", q(f"max by(state)(max_over_time(pg_stat_activity_count{{datname='vikunja',state=~'active|idle|idle in transaction'}}[{d}s]))", e))
    print(" db exec ms/s avg:", q(f"sum(avg_over_time(rate(pg_stat_statements_kind_total_exec_time[1m]){R}))", e),
          "max:", q(f"max_over_time(sum(rate(pg_stat_statements_kind_total_exec_time[1m])){R})", e))
    print(" db plan ms/s avg:", q(f"sum(avg_over_time(rate(pg_stat_statements_kind_total_plan_time[1m]){R}))", e))
    print(" statements/s avg:", q(f"sum(avg_over_time(rate(pg_stat_statements_kind_calls[1m]){R}))", e))
    print(" vikunja net tx MB/s avg:", q(f"sum(avg_over_time(rate(node_network_transmit_bytes_total{{host='vikunja',device!~'lo|docker.*|veth.*|br.*'}}[1m]){R}))/1e6", e))
    print(" loadgen TCP alloc max:", q(f"max_over_time(node_sockstat_TCP_alloc{{host='loadgen'}}[{d}s])", e),
          "TIME_WAIT max:", q(f"max_over_time(node_sockstat_TCP_tw{{host='loadgen'}}[{d}s])", e))
