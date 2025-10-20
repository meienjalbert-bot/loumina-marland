from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import os
from agents.archiviste import propose_sources

router = APIRouter()


class AskReq(BaseModel):
    query: str
    mode: Optional[str] = "answer"
    max_cost: Optional[float] = None
    k: int = 5
    alpha: float = 0.6
    half_life_days: float = float(os.getenv("LOUMINA_FRESHNESS_HALFLIFE", "30"))


@router.post("/parliament/ask")
def ask(req: AskReq) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())
    sources = propose_sources(
        req.query, k=req.k, alpha=req.alpha, half_life_days=req.half_life_days
    )
    votes = [{"agent": "Archiviste", "score": s["scores"]["final"]} for s in sources]
    return {
        "trace_id": trace_id,
        "answer": f"Propositions (hybride, alpha={req.alpha}, t½={req.half_life_days} j).",
        "sources": sources,
        "votes": votes,
        "audit_trace_id": trace_id,
    }
