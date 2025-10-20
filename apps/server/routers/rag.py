from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import pathlib
import os

from apps.server.utils.indexer import INDEX, rebuild
from apps.server.utils.rerank import rerank_cosine
from apps.server.utils.vector_index import VSTORE

router = APIRouter()

# Racine par défaut = racine du repo dans l'image
DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[3]
ALLOWED_EXTS = set(os.getenv("LOUMINA_EXTS", ".md,.txt,.py").split(","))


class IngestReq(BaseModel):
    exts: Optional[List[str]] = None
    path: Optional[str] = None  # ex: "/data"


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


# --------- Dense (HNSW) ---------


class IngestDenseReq(BaseModel):
    exts: Optional[List[str]] = None
    path: Optional[str] = None
    max_vocab: int = 4096


@router.post("/ingest_dense")
def ingest_dense(req: IngestDenseReq) -> Dict[str, Any]:
    root = pathlib.Path(req.path).resolve() if req.path else DEFAULT_ROOT
    allowed = set(req.exts) if req.exts else ALLOWED_EXTS
    stats = VSTORE.build(root, allowed, max_vocab=req.max_vocab)
    return {"ok": True, "root": str(root), "stats": stats}


class DenseQuery(BaseModel):
    query: str
    k: int = 5


@router.post("/query_dense")
def query_dense(body: DenseQuery) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())
    hits = VSTORE.search(body.query, body.k)
    if not hits:
        return {
            "trace_id": trace_id,
            "answer": "Index dense vide. Lance /ingest_dense d'abord.",
            "sources": [],
        }
    return {
        "trace_id": trace_id,
        "answer": f"{len(hits)} résultats (HNSW cosine).",
        "sources": hits,
    }


# --------- Hybride (BM25 + Dense + fraîcheur) ---------


class HybridQuery(BaseModel):
    query: str
    k: int = 5
    alpha: float = 0.6  # poids BM25_n
    half_life_days: float = float(os.getenv("LOUMINA_FRESHNESS_HALFLIFE", "30"))


@router.post("/query_hybrid")
def query_hybrid(body: HybridQuery) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())
    kx = max(10, body.k * 2)

    bm_hits = INDEX.search(body.query, kx) or []
    dn_hits = VSTORE.search(body.query, kx) or []

    if not bm_hits and not dn_hits:
        return {
            "trace_id": trace_id,
            "answer": "Index(s) vide(s). Lance /ingest et/ou /ingest_dense.",
            "sources": [],
        }

    bm_by = {h["doc"]: h for h in bm_hits}
    dn_by = {h["doc"]: h for h in dn_hits}
    docs = set(bm_by) | set(dn_by)

    max_bm = max((h.get("score", 0.0) for h in bm_hits), default=1.0) or 1.0

    out: List[Dict[str, Any]] = []
    for doc in docs:
        bm = bm_by.get(doc, {})
        dn = dn_by.get(doc, {})

        bm25_raw = float(bm.get("score", 0.0))
        bm25_n = bm25_raw / max_bm if max_bm else 0.0
        dense = float(dn.get("score", 0.0))

        # fraîcheur (demi-vie) : on prend l'âge (jours) le plus informatif
        age_b = float(bm.get("age_days", 1e9))
        age_d = float(dn.get("age_days", 1e9))
        age = min(age_b, age_d)
        if age == 1e9:
            age = float(bm.get("age_days", dn.get("age_days", 0.0)))

        decay = pow(0.5, (age / max(1e-6, body.half_life_days)))
        final = (body.alpha * bm25_n + (1.0 - body.alpha) * dense) * decay

        snippet = bm.get("snippet") or dn.get("snippet") or ""
        out.append(
            {
                "doc": doc,
                "snippet": snippet,
                "scores": {
                    "bm25": bm25_raw,
                    "bm25_n": bm25_n,
                    "dense": dense,
                    "decay": decay,
                    "final": final,
                },
            }
        )

    out.sort(key=lambda x: x["scores"]["final"], reverse=True)
    out = out[: body.k]

    answer = (
        f"Hybride: top {len(out)} (alpha={body.alpha}, t½={body.half_life_days} j)."
    )
    return {"trace_id": trace_id, "answer": answer, "sources": out}
