from __future__ import annotations

import time
from typing import Dict

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from apps.server.middleware.trace import TraceMiddleware
from apps.server.routers.parliament import router as parliament_router
from apps.server.routers.rag import router as rag_router


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())


app = FastAPI(
    default_response_class=ORJSONResponse,
    title="Loumina API",
    version="0.1.0-alpha",
)

# 🔔 active le middleware de traces (p50/p95)
app.add_middleware(TraceMiddleware)

# Routers
app.include_router(rag_router)
app.include_router(parliament_router)


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "ts": _now_iso()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.server.main:app", host="0.0.0.0", port=8080, reload=False)
