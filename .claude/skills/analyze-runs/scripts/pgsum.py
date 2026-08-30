#!/usr/bin/env python3
"""Summarize pg-top-statements.txt (psql -x output) of one or more runs: share of total DB time per statement."""
import re, sys

for f in sys.argv[1:]:
    recs, cur = [], {}
    for line in open(f):
        if line.startswith("-[ RECORD"):
            if cur:
                recs.append(cur)
            cur = {}
        elif "|" in line:
            k, v = line.split("|", 1)
            cur[k.strip()] = v.strip()
    if cur:
        recs.append(cur)
    tot = sum(float(r.get("total_ms", 0)) for r in recs) or 1
    print("=====", f)
    print(f"{'total_ms':>9} {'%':>5} {'calls':>8} {'mean':>7} {'plan':>6} {'rows':>9} {'blks_hit':>10} query")
    for r in recs[:25]:
        q = re.sub(r"\s+", " ", r["query"])[:140]
        print(f"{float(r['total_ms']):9.0f} {100*float(r['total_ms'])/tot:5.1f} {r['calls']:>8} {r['mean_ms']:>7} "
              f"{r.get('mean_plan_ms','-'):>6} {r['rows']:>9} {r['shared_blks_hit']:>10} {q}")
