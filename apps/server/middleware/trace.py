import time
import uuid
import orjson
import sys
import os
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from collections import deque


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class _LatencyStats:
    def __init__(self, window: int = 200, every: int = 10):
        self.window = window
        self.every = every
        self.buf = deque(maxlen=window)
        self.n = 0

    def add(self, ms: float):
        self.buf.append(ms)
        self.n += 1
        if self.n % self.every == 0 and self.buf:
            arr = sorted(self.buf)

            def pct(p):
                if len(arr) == 1:
                    return arr[0]
                i = max(0, min(len(arr) - 1, int(round(p * (len(arr) - 1)))))
                return arr[i]

            p50 = pct(0.50)
            p95 = pct(0.95)
            sys.stdout.write(
                orjson.dumps(
                    {
                        "ts": _now_iso(),
                        "lvl": "info",
                        "type": "metrics",
                        "window": self.window,
                        "count": len(arr),
                        "p50_ms": round(p50, 2),
                        "p95_ms": round(p95, 2),
                    }
                ).decode()
                + "\n"
            )
            sys.stdout.flush()


_LAT = _LatencyStats(
    window=int(os.getenv("LOUMINA_METRICS_WINDOW", "200")),
    every=int(os.getenv("LOUMINA_METRICS_EVERY", "10")),
)


class TraceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        t0 = time.perf_counter()
        trace_id = request.headers.get("x-trace-id") or uuid.uuid4().hex
        request.state.trace_id = trace_id
        try:
            response = await call_next(request)
        except Exception as exc:
            dt = (time.perf_counter() - t0) * 1000.0
            log = {
                "ts": _now_iso(),
                "lvl": "error",
                "type": "http",
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "ms": round(dt, 2),
                "err": repr(exc),
            }
            sys.stdout.write(orjson.dumps(log).decode() + "\n")
            sys.stdout.flush()
            raise

        dt = (time.perf_counter() - t0) * 1000.0
        response.headers["X-Trace-Id"] = trace_id
        _LAT.add(dt)

        client = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        log = {
            "ts": _now_iso(),
            "lvl": "info",
            "type": "http",
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": round(dt, 2),
            "ip": client,
            "ua": ua,
        }
        sys.stdout.write(orjson.dumps(log).decode() + "\n")
        sys.stdout.flush()
        return response
