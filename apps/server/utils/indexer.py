from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Iterable, Optional
import pathlib
import re
import threading
import time
from rank_bm25 import BM25Okapi


@dataclass
class Doc:
    path: str
    text: str
    mtime: float  # epoch seconds


class BM25Index:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._docs: List[Doc] = []
        self._tokens: List[List[str]] = []
        self._bm25: Optional[BM25Okapi] = None
        self._built_at: float = 0.0

    @staticmethod
    def _tok(txt: str) -> List[str]:
        return re.findall(r"\w{2,}", txt.lower())

    def build(self, docs: Iterable[Doc]):
        with self._lock:
            self._docs = list(docs)
            self._tokens = [self._tok(d.text) for d in self._docs]
            self._bm25 = BM25Okapi(self._tokens) if self._tokens else None
            self._built_at = time.time()
            return {"docs": len(self._docs), "tokens_lists": len(self._tokens)}

    def search(self, query: str, k: int = 5) -> List[Dict]:
        with self._lock:
            if not self._bm25 or not self._docs:
                return []
            q = self._tok(query)
            scores = self._bm25.get_scores(q)
            top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            now = time.time()
            res = []
            for i in top:
                d = self._docs[i]
                age_days = max(0.0, (now - d.mtime) / 86400.0)
                snippet = d.text[:280].replace("\n", " ")
                res.append(
                    {
                        "doc": d.path,
                        "score": float(scores[i]),
                        "snippet": snippet,
                        "age_days": age_days,
                    }
                )
            return res

    def stats(self) -> Dict[str, float]:
        with self._lock:
            return {"docs": len(self._docs), "built_at": self._built_at}


DEFAULT_EXTS = {".md", ".txt", ".py"}


def load_corpus(root: pathlib.Path, exts: Optional[Iterable[str]] = None) -> List[Doc]:
    exts = set(exts or DEFAULT_EXTS)
    docs: List[Doc] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in exts:
            continue
        if any(
            part in {".venv", "node_modules", "dist", "build", ".git"}
            for part in p.parts
        ):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            rel = str(p.relative_to(root))
            mtime = p.stat().st_mtime
            docs.append(Doc(path=rel, text=txt, mtime=mtime))
        except Exception:
            pass
    return docs


# index global
INDEX = BM25Index()


def rebuild(root: pathlib.Path, allowed_exts: Optional[Iterable[str]] = None):
    from .indexer import load_corpus  # self-import safe

    docs = load_corpus(root, allowed_exts)
    return INDEX.build(docs)
