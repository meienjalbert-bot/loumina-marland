from typing import List, Dict
from apps.server.utils.indexer import INDEX


def propose_sources(query: str, k: int = 5) -> List[Dict]:
    # Récupère directement les meilleurs passages depuis l'index
    hits = INDEX.search(query, k)
    # Adapter le format attendu par les autres agents
    sources = []
    for h in hits:
        sources.append(
            {
                "doc": h["doc"],
                "loc": "n/a",
                "snippet": h.get("snippet", ""),
                "score": h.get("score", 0.0),
            }
        )
    return sources
