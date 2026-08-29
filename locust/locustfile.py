"""Locust user classes modelled on two weeks of Vikunja Cloud access logs (see README).

Classes (pick with `locust ... Worker Glancer IntegrationBot Collaborator`):
  Worker          long interactive session: projects, kanban, task details, edits. Holds a websocket.
  Glancer         short session: open app, look at overview, leave; comes back later. Login churn.
  IntegrationBot  API client with no think time polling tasks/projects (80% of real cloud traffic).
  Collaborator    works in team-shared projects: comments, assigns -> generates notifications over WS.
"""
import os
import random
import time
from itertools import count

import gevent
from locust import FastHttpUser, events, task, tag

from common import (API, PASSWORD, gantt_params, home_params, list_view_params, load_state,
                    lognormal_wait, random_due_date, task_title)
from ws_client import VikunjaWS

STATE = load_state()
_account = count()


def weight(name, default):
    return int(os.environ.get(f"WEIGHT_{name}", default))


class VikunjaUser(FastHttpUser):
    abstract = True
    connection_timeout = 30
    network_timeout = 60

    def on_start(self):
        self.account = STATE["users"][next(_account) % len(STATE["users"])]
        self.projects = self.account["projects"]
        self.token = None
        self.ws = None
        self.login()

    def on_stop(self):
        if self.ws:
            self.ws.close()

    # --- helpers --------------------------------------------------------------
    def login(self):
        r = self.client.post(API + "/login", json={"username": self.account["username"], "password": PASSWORD},
                             name="/login")
        self.token = r.json()["token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"

    def get(self, path, name, **kw):
        return self.client.get(API + path, name=name, **kw)

    def project(self):
        return random.choice(self.projects)

    def task_of(self, project):
        return random.choice(project["tasks"])

    def open_app(self):
        """What the SPA does on load."""
        self.get("/info", "/info")
        self.get("/user", "/user")
        self.get("/projects", "/projects", params={"is_archived": "true", "expand": "permissions", "per_page": 50})
        self.get("/labels", "/labels")
        self.get("/tasks", "/tasks [home]", params=home_params())

    def connect_ws(self):
        self.ws = VikunjaWS(self.host, self.token)
        self.ws.connect()

    def avatars(self, n=3):
        for _ in range(n):
            self.get(f"/avatar/{random.choice(STATE['users'])['username']}", "/avatar/{username}", params={"size": 50})


class Worker(VikunjaUser):
    weight = weight("WORKER", 3)
    wait_time = lambda self: lognormal_wait(median=15)  # noqa: E731

    def on_start(self):
        super().on_start()
        self.open_app()
        self.connect_ws()
        self.refresher = gevent.spawn(self._refresh_loop)

    def on_stop(self):
        self.refresher.kill(block=False)
        super().on_stop()

    def _refresh_loop(self):
        while True:
            gevent.sleep(600)
            r = self.client.post(API + "/user/token/refresh", name="/user/token/refresh")
            if r.status_code == 200:
                self.token = r.json()["token"]
                self.client.headers["Authorization"] = f"Bearer {self.token}"

    @task(15)
    def home(self):
        self.get("/tasks", "/tasks [home]", params=home_params(with_range=random.random() < 0.3))
        self.avatars(2)

    @task(25)
    def project_list_view(self):
        p = self.project()
        self.get(f"/projects/{p['id']}", "/projects/{id}")
        self.get(f"/projects/{p['id']}/views/{p['views']['list']}/tasks", "/projects/{id}/views/{view}/tasks [list]",
                 params=list_view_params())
        if random.random() < 0.3:
            self.get(f"/projects/{p['id']}/views/{p['views']['list']}/tasks", "/projects/{id}/views/{view}/tasks [list]",
                     params=list_view_params(page=2))
        self.avatars(3)

    @task(10)
    def project_kanban(self):
        p = self.project()
        self.get(f"/projects/{p['id']}", "/projects/{id}")
        self.get(f"/projects/{p['id']}/views/{p['views']['kanban']}/buckets/tasks",
                 "/projects/{id}/views/{view}/buckets/tasks [kanban]", params={"per_page": 25, "filter_timezone": "Europe/Berlin"})
        self.avatars(3)

    @task(12)
    def task_detail(self):
        p = self.project()
        t = self.task_of(p)
        self.get(f"/tasks/{t}", "/tasks/{id}", params={"expand": ["comments", "attachments", "buckets"]})
        self.get(f"/tasks/{t}/comments", "/tasks/{id}/comments")
        self.client.put(API + f"/tasks/{t}/read", name="/tasks/{id}/read")

    @task(6)
    def update_task(self):
        p = self.project()
        t = self.task_of(p)
        change = random.choice([
            {"done": random.random() < 0.6},
            {"title": task_title()},
            {"priority": random.randint(0, 5)},
            {"due_date": random_due_date() or "0001-01-01T00:00:00Z"},
        ])
        self.client.patch(API + f"/tasks/{t}", json=change, name="/tasks/{id} [patch]")

    @task(4)
    def create_task(self):
        p = self.project()
        body = {"title": task_title()}
        if (d := random_due_date()):
            body["due_date"] = d
        r = self.client.post(API + f"/projects/{p['id']}/tasks", json=body, name="/projects/{id}/tasks [create]")
        if r.status_code == 201:
            p["tasks"].append(r.json()["id"])

    @task(3)
    def move_task(self):
        p = self.project()
        t = self.task_of(p)
        if p["buckets"] and random.random() < 0.5:
            self.client.put(API + f"/projects/{p['id']}/views/{p['views']['kanban']}/buckets/{random.choice(p['buckets'])}/tasks",
                            json={"task_id": t}, name="/projects/{id}/views/{view}/buckets/{bucket}/tasks [move]")
        self.client.put(API + f"/tasks/{t}/position",
                        json={"position": random.random() * 65536, "project_view_id": p["views"]["list"]},
                        name="/tasks/{id}/position")

    @task(2)
    def add_label(self):
        p = self.project()
        self.client.post(API + f"/tasks/{self.task_of(p)}/labels", json={"label_id": random.choice(self.account["labels"])},
                         name="/tasks/{id}/labels [add]")

    @task(1)
    def comment(self):
        p = self.project()
        self.client.post(API + f"/tasks/{self.task_of(p)}/comments", json={"comment": f"<p>Comment at {time.time():.0f}</p>"},
                         name="/tasks/{id}/comments [create]")

    @task(2)
    def gantt(self):
        p = self.project()
        self.get(f"/projects/{p['id']}/views/{p['views']['gantt']}/tasks", "/projects/{id}/views/{view}/tasks [gantt]",
                 params=gantt_params())

    @task(1)
    def create_project(self):
        r = self.client.post(API + "/projects", json={"title": f"Project {random.randint(1, 99999)}"}, name="/projects [create]")
        if r.status_code == 201:
            proj = r.json()
            views = {v["view_kind"]: v["id"] for v in proj.get("views") or []}
            if views:
                # give it one task so later reads have something to pick
                t = self.client.post(API + f"/projects/{proj['id']}/tasks", json={"title": task_title()},
                                     name="/projects/{id}/tasks [create]")
                if t.status_code == 201:
                    self.projects.append({"id": proj["id"], "views": views, "buckets": [], "tasks": [t.json()["id"]]})


class Glancer(VikunjaUser):
    """Half of real sessions are ~5 requests long. Login, look, leave, come back minutes later."""
    weight = weight("GLANCER", 3)
    wait_time = lambda self: random.uniform(60, 400)  # noqa: E731

    @task
    def session(self):
        self.login()
        self.open_app()
        ws = VikunjaWS(self.host, self.token)
        ws.connect()
        gevent.sleep(random.uniform(2, 20))
        if random.random() < 0.5:
            p = self.project()
            self.get(f"/projects/{p['id']}/views/{p['views']['list']}/tasks", "/projects/{id}/views/{view}/tasks [list]",
                     params=list_view_params())
        ws.close()


class IntegrationBot(VikunjaUser):
    """Home Assistant / node scripts: no think time, hammer reads. 3 IPs made 1.5M of 3.5M cloud requests."""
    weight = weight("BOT", 1)
    wait_time = lambda self: random.uniform(0.2, 2)  # noqa: E731

    @task(65)
    def get_task(self):
        p = self.project()
        self.get(f"/tasks/{self.task_of(p)}", "/tasks/{id} [bot]")

    @task(23)
    def list_project_tasks(self):
        p = self.project()
        self.get(f"/projects/{p['id']}/tasks", "/projects/{id}/tasks [bot]",
                 params={"per_page": random.choice([20, 50]), "page": 1, "filter": random.choice(["", "done = false"])})

    @task(9)
    def list_projects(self):
        self.get("/projects", "/projects [bot]", params={"per_page": 50})

    @task(3)
    def all_tasks(self):
        self.get("/tasks", "/tasks [bot]", params={"per_page": 100, "sort_by": ["priority", "due_date"],
                                                   "order_by": ["desc", "asc"], "filter": "done = false"})


class Collaborator(VikunjaUser):
    """Team member working in the owner's shared project. Comments/assignments notify the owner via WS."""
    weight = weight("COLLAB", 0)
    wait_time = lambda self: lognormal_wait(median=10)  # noqa: E731

    def on_start(self):
        super().on_start()
        if not self.account["shared_projects"]:
            # owners: just sit there connected, receiving notifications
            self.shared = None
        else:
            self.shared = random.choice(self.account["shared_projects"])
        self.open_app()
        self.connect_ws()

    @task(5)
    def read_shared(self):
        p = self.shared or self.project()
        self.get(f"/projects/{p['id']}/views/{p['views']['list']}/tasks", "/projects/{id}/views/{view}/tasks [list]",
                 params=list_view_params())

    @task(3)
    def comment(self):
        if not self.shared:
            return
        self.client.post(API + f"/tasks/{self.task_of(self.shared)}/comments",
                         json={"comment": f"<p>Ping from {self.account['username']}</p>"}, name="/tasks/{id}/comments [create]")

    @task(2)
    def assign_owner(self):
        if not self.shared:
            return
        self.client.post(API + f"/tasks/{self.task_of(self.shared)}/assignees",
                         json={"user_id": self.shared["owner_id"]}, name="/tasks/{id}/assignees [add]")

    @task(2)
    def toggle_done(self):
        if not self.shared:
            return
        self.client.patch(API + f"/tasks/{self.task_of(self.shared)}", json={"done": random.random() < 0.5},
                          name="/tasks/{id} [patch]")

    @task(1)
    def notifications(self):
        self.get("/notifications", "/notifications", params={"page": 1})


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--seed-state", default=None, help="path to seed-state.json (default: next to locustfile)")
