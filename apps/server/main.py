from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import uvicorn
from datetime import datetime, timezone
from typing import Dict

from apps.server.routers.parliament import router as parliament_router
from apps.server.routers.rag import router as rag_router

app = FastAPI(
    default_response_class=ORJSONResponse, title="Loumina API", version="0.1.0-alpha"
)
app.include_router(parliament_router, prefix="/parliament", tags=["parliament"])
app.include_router(rag_router, tags=["rag"])


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    uvicorn.run("apps.server.main:app", host="0.0.0.0", port=8080, reload=False)
