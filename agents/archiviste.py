from typing import List, Dict
import os

from apps.server.utils.indexer import INDEX
from apps.server.utils.vector_index import VSTORE


def propose_sources(
    query: str, k: int = 5, alpha: float = 0.6, half_life_days: float | None = None
) -> List[Dict]:
    if half_life_days is None:
        half_life_days = float(os.getenv("LOUMINA_FRESHNESS_HALFLIFE", "30"))

    kx = max(10, k * 2)
    bm = INDEX.search(query, kx) or []
    dn = VSTORE.search(query, kx) or []

    bm_by = {h["doc"]: h for h in bm}
    dn_by = {h["doc"]: h for h in dn}
    docs = set(bm_by) | set(dn_by)

    max_bm = max((h.get("score", 0.0) for h in bm), default=1.0) or 1.0
    out: List[Dict] = []
    for d in docs:
        b = bm_by.get(d, {})
        n = dn_by.get(d, {})
        bm25_raw = float(b.get("score", 0.0))
        bm25_n = bm25_raw / max_bm if max_bm else 0.0
        dense = float(n.get("score", 0.0))

        age_b = float(b.get("age_days", 1e9))
        age_d = float(n.get("age_days", 1e9))
        age = min(age_b, age_d)
        if age == 1e9:
            age = float(b.get("age_days", n.get("age_days", 0.0)))

        decay = pow(0.5, (age / max(1e-6, half_life_days)))
        final = (alpha * bm25_n + (1.0 - alpha) * dense) * decay
        snippet = b.get("snippet") or n.get("snippet") or ""

        out.append(
            {
                "doc": d,
                "loc": "n/a",
                "snippet": snippet,
                "age_days": age,
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
    return out[:k]
