#!/usr/bin/env python3
"""Seeds a Vikunja instance via the v2 API and writes seed-state.json for the locust users.

  python seed.py --host http://10.0.1.3:3456 --users 100 --projects 5 --tasks 80

Layout per user: N top-level projects, one of them with a nested child; labels; tasks spread over
projects with mixed due dates / priorities / done state; some comments. Every 5 users form a team
that gets write access to the first user's first project (collaboration scenario).
"""
import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from common import API, PASSWORD, STATE_FILE, random_due_date, task_title, iso, now
from datetime import timedelta

ap = argparse.ArgumentParser()
ap.add_argument("--host", required=True)
ap.add_argument("--users", type=int, default=100)
ap.add_argument("--projects", type=int, default=5, help="top-level projects per user")
ap.add_argument("--tasks", type=int, default=80, help="tasks per project")
ap.add_argument("--labels", type=int, default=6)
ap.add_argument("--team-size", type=int, default=5)
ap.add_argument("--concurrency", type=int, default=16)
ap.add_argument("--prefix", default="perf")
args = ap.parse_args()

S = requests.Session()
S.headers["Content-Type"] = "application/json"


TOKENS = {}


def login(username):
    r = S.post(args.host + API + "/login", json={"username": username, "password": PASSWORD, "long_token": True}, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"login {username}: {r.status_code} {r.text[:200]}")
    TOKENS[username] = r.json()["token"]
    return TOKENS[username]


def call(method, path, user=None, ok=(200, 201), **kw):
    """user = username; tokens are short-lived, so re-login on 401."""
    for attempt in range(5):
        h = {"Authorization": f"Bearer {TOKENS.get(user) or login(user)}"} if user else {}
        r = S.request(method, args.host + API + path, headers=h, timeout=60, **kw)
        if r.status_code in ok:
            return r.json() if r.content else None
        if r.status_code == 401 and user:
            login(user)
            continue
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1 + attempt)
            continue
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
    raise RuntimeError(f"{method} {path} kept failing")


def ensure_user(i):
    username = f"{args.prefix}{i}"
    r = S.post(args.host + API + "/register", json={"username": username, "password": PASSWORD,
                                                     "email": f"{username}@example.invalid"})
    if r.status_code not in (200, 201, 400, 409):  # 400/409: exists
        raise RuntimeError(f"register {username}: {r.status_code} {r.text[:200]}")
    me = call("GET", "/user", username)
    return {"username": username, "id": me["id"]}


def views_of(project):
    return {v["view_kind"]: v["id"] for v in project.get("views") or []}


def seed_user(u):
    tok = u["username"]
    labels = [call("POST", "/labels", tok, json={"title": f"label-{u['username']}-{i}",
                                                 "hex_color": "%06x" % random.randint(0, 0xFFFFFF)})["id"]
              for i in range(args.labels)]
    projects = []
    for p in range(args.projects):
        proj = call("POST", "/projects", tok, json={"title": f"{u['username']} project {p}"})
        projects.append(proj)
        if p == 0:  # one nested child, like the ~2 level trees common in real data
            child = call("POST", "/projects", tok, json={"title": f"{u['username']} sub {p}", "parent_project_id": proj["id"]})
            projects.append(child)

    out_projects = []
    for proj in projects:
        views = views_of(proj)
        if not views:
            views = views_of({"views": call("GET", f"/projects/{proj['id']}/views", tok)["items"]})
        tasks = []
        batch = []
        for t in range(args.tasks):
            task = {"title": task_title(), "priority": random.choice([0, 0, 0, 1, 2, 3, 4, 5]),
                    "done": random.random() < 0.3,
                    "description": "<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>" if random.random() < 0.4 else ""}
            due = random_due_date()
            if due:
                task["due_date"] = due
            if random.random() < 0.15:  # gantt fodder
                start = now() + timedelta(days=random.randint(-10, 40))
                task["start_date"] = iso(start)
                task["end_date"] = iso(start + timedelta(days=random.randint(1, 14)))
            batch.append(task)
            if len(batch) == 100 or t == args.tasks - 1:
                created = call("POST", f"/projects/{proj['id']}/tasks/bulk", tok, json={"tasks": batch})
                tasks.extend(x["id"] for x in created["tasks"])
                batch = []
        for tid in random.sample(tasks, k=max(1, len(tasks) // 4)):
            call("POST", f"/tasks/{tid}/labels", tok, json={"label_id": random.choice(labels)})
        for tid in random.sample(tasks, k=max(1, len(tasks) // 10)):
            call("POST", f"/tasks/{tid}/comments", tok, json={"comment": "<p>Seeded comment, nothing to see here.</p>"})
        buckets = []
        if "kanban" in views:
            buckets = [b["id"] for b in call("GET", f"/projects/{proj['id']}/views/{views['kanban']}/buckets", tok)["items"]]
        out_projects.append({"id": proj["id"], "views": views, "buckets": buckets, "tasks": tasks})
    u["labels"] = labels
    u["projects"] = out_projects
    u["shared_projects"] = []
    return u


def seed_teams(users):
    for i in range(0, len(users), args.team_size):
        group = users[i:i + args.team_size]
        if len(group) < 2:
            continue
        owner = group[0]
        tok = owner["username"]
        team = call("POST", "/teams", tok, json={"name": f"team-{owner['username']}"})
        for m in group[1:]:
            call("POST", f"/teams/{team['id']}/members", tok, json={"username": m["username"]})
        shared = owner["projects"][0]
        call("POST", f"/projects/{shared['id']}/teams", tok, json={"team_id": team["id"], "permission": 1})
        for m in group[1:]:
            m["shared_projects"].append({**shared, "owner_id": owner["id"]})
        owner["team_members"] = [m["id"] for m in group[1:]]


t0 = time.time()
print(f"registering {args.users} users", flush=True)
with ThreadPoolExecutor(args.concurrency) as ex:
    users = list(ex.map(ensure_user, range(1, args.users + 1)))
print(f"seeding {len(users)} users x {args.projects + 1} projects x {args.tasks} tasks", flush=True)
done_users, done_tasks, t1 = [], 0, time.time()
with ThreadPoolExecutor(args.concurrency) as ex:
    for fut in as_completed([ex.submit(seed_user, u) for u in users]):
        u = fut.result()
        done_users.append(u)
        done_tasks += sum(len(p["tasks"]) for p in u["projects"])
        n, el = len(done_users), time.time() - t1
        print(f"  {n}/{len(users)} users, {done_tasks} tasks, {done_tasks / el:.0f} tasks/s, "
              f"eta {el / n * (len(users) - n):.0f}s", flush=True)
users = sorted(done_users, key=lambda u: u["id"])
print("teams", flush=True)
seed_teams(users)
json.dump({"host": args.host, "users": users}, open(STATE_FILE, "w"))
total_tasks = sum(len(p["tasks"]) for u in users for p in u["projects"])
print(f"done in {time.time() - t0:.0f}s: {len(users)} users, {total_tasks} tasks -> {STATE_FILE}")
