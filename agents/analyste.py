from typing import List, Dict


def propose_answer(query: str, sources: List[Dict]) -> Dict:
    citations = [{"doc": s["doc"], "loc": s["loc"]} for s in sources[:2]]
    answer = f"Réponse (draft) à: '{query}'. " f"Basée sur {len(sources)} source(s)."
    return {"answer": answer, "sources": citations}
