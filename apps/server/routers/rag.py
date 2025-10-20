from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import pathlib
import os

from apps.server.utils.indexer import INDEX, rebuild

router = APIRouter()

# Racine d'ingestion: par défaut, la racine du repo
ROOT = pathlib.Path(__file__).resolve().parents[3]
ALLOWED_EXTS = set(os.getenv("LOUMINA_EXTS", ".md,.txt,.py").split(","))


class IngestReq(BaseModel):
    exts: Optional[List[str]] = None  # ex: [".md",".txt"]
    # plus tard: paths ciblés


class Query(BaseModel):
    query: str
    k: int = 5


@router.post("/ingest")
def rag_ingest(req: IngestReq) -> Dict[str, Any]:
    allowed = set(req.exts) if req.exts else ALLOWED_EXTS
    stats = rebuild(ROOT, allowed)
    return {"ok": True, "root": str(ROOT), "exts": list(allowed), "stats": stats}


@router.post("/query")
def rag_query(body: Query) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())
    hits = INDEX.search(body.query, body.k)
    if not hits:
        return {
            "trace_id": trace_id,
            "answer": "Index vide. Lance /ingest d'abord.",
            "sources": [],
        }
    answer = f"Top {len(hits)} sources locales pour: “{body.query}”."
    return {"trace_id": trace_id, "answer": answer, "sources": hits}
