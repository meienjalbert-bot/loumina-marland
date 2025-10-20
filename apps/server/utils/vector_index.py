from __future__ import annotations
from typing import List, Dict, Iterable, Optional
from dataclasses import dataclass
from collections import Counter
import numpy as np
import hnswlib
import pathlib
import os
import json
import re
import time

from apps.server.utils.indexer import Doc, load_corpus

STATE_DIR = pathlib.Path(os.getenv("LOUMINA_STATE", "/app/state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = STATE_DIR / "dense.index"
META_PATH = STATE_DIR / "dense_meta.json"

_TOKEN_RE = re.compile(r"\w{2,}")


def _tok(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class DenseMeta:
    dim: int
    vocab: List[str]
    docs: List[Dict]  # [{"id":int,"path":str,"len":int,"snippet":str,"mtime":float}]


class DenseStore:
    def __init__(self) -> None:
        self.index: Optional[hnswlib.Index] = None
        self.meta: Optional[DenseMeta] = None
        self.v2i: Dict[str, int] = {}

    def _build_vocab(self, docs: List[Doc], max_vocab: int = 4096) -> List[str]:
        cnt = Counter()
        for d in docs:
            cnt.update(_tok(d.text))
        return [w for w, _ in cnt.most_common(max_vocab)]

    def _embed(self, text: str) -> np.ndarray:
        dim = len(self.v2i)
        if dim <= 0:
            return np.zeros(1, dtype=np.float32)
        vec = np.zeros(dim, dtype=np.float32)
        for w in _tok(text):
            i = self.v2i.get(w)
            if i is not None:
                vec[i] += 1.0
        n = np.linalg.norm(vec)
        if n > 0:
            vec /= n
        return vec

    def build(
        self,
        root: pathlib.Path,
        exts: Optional[Iterable[str]] = None,
        max_vocab: int = 4096,
    ) -> Dict[str, int]:
        docs = load_corpus(root, exts)
        vocab = self._build_vocab(docs, max_vocab=max_vocab)
        self.v2i = {w: i for i, w in enumerate(vocab)}
        dim = len(self.v2i) if self.v2i else 1

        index = hnswlib.Index(space="cosine", dim=dim)
        index.init_index(max_elements=max(1, len(docs)), ef_construction=200, M=16)
        index.set_ef(100)

        metas: List[Dict] = []
        for i, d in enumerate(docs):
            vec = self._embed(d.text)
            index.add_items(vec, i)
            metas.append(
                {
                    "id": i,
                    "path": d.path,
                    "len": len(d.text),
                    "snippet": d.text[:280].replace("\n", " "),
                    "mtime": d.mtime,
                }
            )

        self.index = index
        self.meta = DenseMeta(dim=dim, vocab=list(self.v2i.keys()), docs=metas)
        self._save()
        return {"docs": len(docs), "dim": dim}

    def _save(self) -> None:
        assert self.index is not None and self.meta is not None
        self.index.save_index(str(INDEX_PATH))
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "dim": self.meta.dim,
                    "vocab": self.meta.vocab,
                    "docs": self.meta.docs,
                },
                f,
            )

    def _load(self) -> bool:
        if not INDEX_PATH.exists() or not META_PATH.exists():
            return False
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.meta = DenseMeta(dim=meta["dim"], vocab=meta["vocab"], docs=meta["docs"])
        self.v2i = {w: i for i, w in enumerate(self.meta.vocab)}
        self.index = hnswlib.Index(
            space="cosine", dim=self.meta.dim if self.meta.dim > 0 else 1
        )
        self.index.load_index(str(INDEX_PATH))
        self.index.set_ef(100)
        return True

    def ensure_loaded(self) -> bool:
        if self.index is None or self.meta is None:
            return self._load()
        return True

    def search(self, query: str, k: int = 5) -> List[Dict]:
        if (
            not self.ensure_loaded()
            or self.meta is None
            or self.index is None
            or self.meta.dim == 0
        ):
            return []
        current = self.index.get_current_count()
        if current <= 0:
            return []
        k_eff = min(max(1, k), current)
        self.index.set_ef(max(50, k_eff))
        q = self._embed(query)
        labels, dists = self.index.knn_query(q, k=k_eff)
        now = time.time()
        out: List[Dict] = []
        for lab, dist in zip(labels[0].tolist(), dists[0].tolist()):
            doc = self.meta.docs[lab]
            score = 1.0 - float(dist)
            age_days = max(0.0, (now - float(doc.get("mtime", now))) / 86400.0)
            out.append(
                {
                    "doc": doc["path"],
                    "score": score,
                    "snippet": doc["snippet"],
                    "age_days": age_days,
                }
            )
        return out


VSTORE = DenseStore()
