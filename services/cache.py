"""
Simple thread-safe in-memory TTL cache.
Works for warm server processes (local + Vercel warm lambdas).
"""
import threading
from datetime import datetime

_store: dict = {}
_lock = threading.Lock()


def cached(key: str, fn, ttl: int = 120):
    """Return cached value if fresh, else run fn(), store and return result."""
    with _lock:
        entry = _store.get(key)
        if entry and (datetime.now().timestamp() - entry["ts"]) < ttl:
            return entry["val"]
    val = fn()
    with _lock:
        _store[key] = {"val": val, "ts": datetime.now().timestamp()}
    return val


def invalidate(prefix: str = ""):
    """Invalidate all keys matching prefix (or all if empty)."""
    with _lock:
        if not prefix:
            _store.clear()
        else:
            for k in list(_store.keys()):
                if k.startswith(prefix):
                    del _store[k]
