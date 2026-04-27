"""
core/sse.py

Thread-safe Server-Sent Events bus.

Each class gets its own subscriber list.  When a client connects to
/<class>/stream, it gets a Queue and receives every subsequent event.
A snapshot of current session state is sent on connect so late-joiners
catch up instantly.

Usage:
    from core import sse
    sse.push("cecs460", {"type": "submission", ...})
"""
import json
import queue
import threading
from collections import defaultdict

_lock        = threading.Lock()
_subscribers: dict[str, list[queue.Queue]] = defaultdict(list)


def subscribe(class_id: str) -> queue.Queue:
    q = queue.Queue(maxsize=100)
    with _lock:
        _subscribers[class_id].append(q)
    return q


def unsubscribe(class_id: str, q: queue.Queue) -> None:
    with _lock:
        try:
            _subscribers[class_id].remove(q)
        except ValueError:
            pass


def push(class_id: str, event: dict) -> None:
    """Broadcast an event to all connected clients for this class."""
    msg  = f"data: {json.dumps(event)}\n\n"
    dead = []
    with _lock:
        subs = list(_subscribers[class_id])
    for q in subs:
        try:
            q.put_nowait(msg)
        except queue.Full:
            dead.append(q)
    for q in dead:
        unsubscribe(class_id, q)
