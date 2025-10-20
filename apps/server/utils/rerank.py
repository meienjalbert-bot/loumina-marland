from __future__ import annotations
from typing import List, Dict
from collections import Counter
import math
import re


def _tok(t: str) -> List[str]:
    """Tokenisation simple (mots de 2+ lettres, minuscules)."""
    return re.findall(r"\w{2,}", t.lower())


def _cosine_dict(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[t] * b.get(t, 0.0) for t in a.keys())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return (dot / (na * nb)) if (na and nb) else 0.0


def _tf(text: str) -> Dict[str, float]:
    c = Counter(_tok(text))
    if not c:
        return {}
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}


def rerank_cosine(query: str, hits: List[Dict], alpha: float = 0.6) -> List[Dict]:
    """Combine BM25 normalisé + cosinus TF(simple) sur le snippet."""
    if not hits:
        return hits
    qtf = _tf(query)
    max_bm25 = max(h.get("score", 0.0) for h in hits) or 1.0
    out: List[Dict] = []
    for h in hits:
        bm25n = h.get("score", 0.0) / max_bm25
        cos = _cosine_dict(qtf, _tf(h.get("snippet", "")))
        sc = alpha * bm25n + (1 - alpha) * cos
        hh = dict(h)
        hh["rerank"] = {"bm25_n": bm25n, "cosine": cos, "score": sc}
        out.append(hh)
    out.sort(key=lambda x: x["rerank"]["score"], reverse=True)
    return out
