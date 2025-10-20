from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import pathlib
import os

from apps.server.utils.indexer import INDEX, rebuild
from apps.server.utils.rerank import rerank_cosine

router = APIRouter()

# Racine par défaut (repo)
DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[3]
ALLOWED_EXTS = set(os.getenv("LOUMINA_EXTS", ".md,.txt,.py").split(","))


class IngestReq(BaseModel):
    exts: Optional[List[str]] = None  # ex: [".md",".txt"]
    path: Optional[str] = None  # ex: "/data/docs"


class Query(BaseModel):
    query: str
    k: int = 5


@router.post("/ingest")
def rag_ingest(req: IngestReq) -> Dict[str, Any]:
    root = pathlib.Path(req.path).resolve() if req.path else DEFAULT_ROOT
    allowed = set(req.exts) if req.exts else ALLOWED_EXTS
    stats = rebuild(root, allowed)
    return {"ok": True, "root": str(root), "exts": list(allowed), "stats": stats}


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
    reranked = rerank_cosine(body.query, hits, alpha=0.6)
    answer = f"Top {len(reranked)} sources locales pour: “{body.query}”."
    return {"trace_id": trace_id, "answer": answer, "sources": reranked}
