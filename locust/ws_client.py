"""Minimal Vikunja websocket client for locust users.

Protocol: upgrade without auth, then {"action":"auth","token":JWT} -> {"action":"auth.success"},
then {"action":"subscribe","event":"notification.created"}. Server pings every 30s; websocket-client pongs.
"""
import json
import time
from datetime import datetime, timezone

import gevent
import websocket
from locust import events


def _fire(name, start, exc=None, length=0):
    events.request.fire(request_type="WS", name=name, response_time=(time.time() - start) * 1000,
                        response_length=length, exception=exc, context={})


class VikunjaWS:
    def __init__(self, host, token, subscriptions=("notification.created",)):
        self.url = host.replace("http://", "ws://").replace("https://", "wss://") + "/api/v2/ws"
        self.token = token
        self.subscriptions = subscriptions
        self.ws = None
        self.reader = None
        self.received = 0

    def connect(self):
        start = time.time()
        try:
            self.ws = websocket.create_connection(self.url, timeout=10)
            self.ws.send(json.dumps({"action": "auth", "token": self.token}))
            reply = json.loads(self.ws.recv())
            if reply.get("action") != "auth.success":
                raise RuntimeError(f"ws auth failed: {reply}")
            for ev in self.subscriptions:
                self.ws.send(json.dumps({"action": "subscribe", "event": ev}))
            _fire("connect+auth+subscribe", start)
        except Exception as e:  # noqa: BLE001
            _fire("connect+auth+subscribe", start, exc=e)
            self.ws = None
            return
        self.ws.settimeout(None)
        self.reader = gevent.spawn(self._read_loop)

    def _read_loop(self):
        while self.ws:
            try:
                raw = self.ws.recv()
            except Exception:  # noqa: BLE001
                return
            if not raw:
                continue
            self.received += 1
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if msg.get("error"):
                _fire(f"error {msg['error']}", time.time(), exc=RuntimeError(msg["error"]))
                continue
            ev = msg.get("event")
            if ev:
                # Delivery latency = now - notification.created (server clock, same NTP pool)
                created = (msg.get("data") or {}).get("created")
                latency_start = time.time()
                if created:
                    try:
                        latency_start = datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp()
                    except ValueError:
                        pass
                _fire(f"push {ev}", latency_start, length=len(raw))

    def close(self):
        ws, self.ws = self.ws, None
        if ws:
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass
        if self.reader:
            self.reader.kill(block=False)
