from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid

from agents.archiviste import propose_sources
from agents.analyste import propose_answer
from agents.securite import review_answer

router = APIRouter()


class Ask(BaseModel):
    query: str
    mode: Optional[str] = "answer"  # "answer" | "plan"


@router.post("/ask")
def parliament_ask(body: Ask) -> Dict[str, Any]:
    trace_id = str(uuid.uuid4())

    # 1) Archiviste : récup squelettes de sources (stub)
    sources = propose_sources(body.query)

    # 2) Analyste : proposition de réponse (synthèse + citations)
    draft = propose_answer(body.query, sources)

    # 3) Sécurité : contre-lecture & score
    reviewed = review_answer(draft)

    # 4) Agrégation simple
    score = max(0.0, 1.0 - reviewed.get("risk", 0.0))
    return {
        "trace_id": trace_id,
        "answer": reviewed["answer"],
        "sources": reviewed["sources"],
        "votes": {"score": score, "risk": reviewed.get("risk", 0.0)},
        "audit": {"agents": ["archiviste", "analyste", "securite"]},
    }
