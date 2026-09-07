#!/usr/bin/env python3
"""Per-endpoint comparison across runs + steady-state vs ramp numbers + timeline of the last run.
Usage: locust_summary.py runs/<ts>-baseline [runs/<ts>-baseline ...]"""
import csv, sys

runs = sys.argv[1:]
data = {r: {row["Name"]: row for row in csv.DictReader(open(r + "/locust_stats.csv"))} for r in runs}
names = sorted(set().union(*[d.keys() for d in data.values()]),
               key=lambda n: -int(data[runs[-1]].get(n, {}).get("Request Count", 0)))
print(f"{'endpoint':58} " + " ".join(f"{'reqs':>7} {'avg':>6} {'p50':>6} {'p95':>6} {'p99':>6} {'fail':>4}|" for _ in runs))
for n in names:
    line = f"{n[:58]:58} "
    for r in runs:
        d = data[r].get(n)
        line += (f"{d['Request Count']:>7} {float(d['Average Response Time']):6.0f} {d['50%']:>6} {d['95%']:>6} "
                 f"{d['99%']:>6} {d['Failure Count']:>4}|") if d else " " * 40 + "|"
    print(line)


def med(k, rs):
    v = sorted(float(x[k]) for x in rs if x[k] not in ("", "N/A"))
    return v[len(v) // 2] if v else float("nan")


print()
for r in runs:
    agg = [x for x in csv.DictReader(open(r + "/locust_stats_history.csv")) if x["Name"] == "Aggregated"]
    target = max(int(x["User Count"]) for x in agg)
    # users that die during the ramp (login retries exhausted) keep the count just below the target
    full = [x for x in agg if int(x["User Count"]) >= 0.97 * target]
    ramp = [x for x in agg if int(x["User Count"]) < 0.97 * target]
    ss = full[len(full) // 2:]  # second half of full-load window
    t0 = int(agg[0]["Timestamp"])
    print(f"{r}: users {target}, ramp {len(ramp)} rows, full-load {len(full)} rows")
    print(f"  steady: rps {med('Requests/s', ss):.0f}  p50 {med('50%', ss):.0f} p95 {med('95%', ss):.0f} p99 {med('99%', ss):.0f}"
          f"   ramp: p50 {med('50%', ramp):.0f} p95 {med('95%', ramp):.0f} p99 {med('99%', ramp):.0f}")
    if full:
        print(f"  steady window unix: {int(full[len(full)//2]['Timestamp'])} .. {int(full[-1]['Timestamp'])}")

print("\ntimeline of last run (t users rps fail/s p50 p95 p99):")
agg = [x for x in csv.DictReader(open(runs[-1] + "/locust_stats_history.csv")) if x["Name"] == "Aggregated"]
t0 = int(agg[0]["Timestamp"])
for x in agg[::20]:
    print(int(x["Timestamp"]) - t0, x["User Count"], f"{float(x['Requests/s']):.0f}", x["Failures/s"], x["50%"], x["95%"], x["99%"])
