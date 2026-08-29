"""Shared helpers: request shapes copied from what the Vikunja frontend sends (see cloud log analysis in README)."""
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone

API = "/api/v2"
TZ = "Europe/Berlin"
STATE_FILE = os.environ.get("SEED_STATE", os.path.join(os.path.dirname(__file__), "seed-state.json"))
PASSWORD = os.environ.get("SEED_PASSWORD", "perf-test-1234")


def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now():
    return datetime.now(timezone.utc)


def random_due_date():
    """Mix seen in real data: most tasks have no due date, some overdue, some upcoming."""
    r = random.random()
    if r < 0.55:
        return None
    if r < 0.7:
        return iso(now() - timedelta(days=random.randint(1, 60)))
    return iso(now() + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23)))


# --- query shapes -----------------------------------------------------------

def home_params(with_range=False):
    p = {
        "sort_by": ["due_date", "id"],
        "order_by": ["asc", "desc"],
        "filter": "done = false",
        "filter_include_nulls": "false",
        "expand": ["comment_count", "is_unread"],
        "filter_timezone": TZ,
        "page": 1,
    }
    if with_range:
        p["filter"] += f" && due_date < '{iso(now() + timedelta(days=7))}' && due_date > '{iso(now() - timedelta(days=30))}'"
    return p


def list_view_params(page=1):
    return {
        "sort_by": ["position"],
        "order_by": ["asc"],
        "filter": "done = false",
        "filter_include_nulls": "false",
        "expand": ["comment_count", "is_unread", "subtasks"],
        "filter_timezone": TZ,
        "per_page": 25,
        "page": page,
    }


def gantt_params():
    start = now() - timedelta(days=random.randint(0, 20))
    return {
        "filter": f'((start_date >= "{start:%Y-%m-%d}" && start_date <= "{start + timedelta(days=70):%Y-%m-%d}") '
                  f'|| (end_date >= "{start:%Y-%m-%d}" && end_date <= "{start + timedelta(days=70):%Y-%m-%d}"))',
        "filter_include_nulls": "false",
        "per_page": 200,
        "sort_by": ["start_date"],
        "order_by": ["asc"],
        "filter_timezone": TZ,
    }


TASK_TITLES = ["Fix login bug", "Write report", "Call supplier", "Prepare slides", "Review PR", "Buy milk",
               "Update docs", "Plan sprint", "Refactor auth", "Send invoice", "Book flights", "Clean garage"]


def task_title():
    return f"{random.choice(TASK_TITLES)} #{random.randint(1, 99999)}"


def lognormal_wait(median=15, sigma=0.9, cap=240):
    """Think time between page actions. Median ~15s, long tail, capped."""
    import math
    return min(random.lognormvariate(math.log(median), sigma), cap)
