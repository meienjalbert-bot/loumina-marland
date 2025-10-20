# Loumina MARLAND — Starter Pack (MVP)

Ce dépôt est un **monorepo** minimal pour démarrer Loumina Nexus / Parlement d’IA local-first.

## Structure
```
apps/
  server/          # FastAPI (API RAG + Parlement)
agents/            # 3 agents sobres: archiviste, analyste, securite
rag/               # pipelines d'ingestion & eval (squelettes)
infra/
  compose/         # compose.pi.yml / compose.worker.yml
  scripts/         # backup/restore Qdrant
  systemd/         # service user rootless
docs/
  adr/             # décisions d'archi
  runbooks/        # procédures (ex: restore Qdrant)
tests/             # tests de base
```

## Démarrage rapide (local)
```bash
# 0) Python 3.11+ recommandé
python3 -V

# 1) Installer dépendances server en dev
python3 -m venv .venv && source .venv/bin/activate
pip install -r apps/server/requirements.txt

# 2) Lancer l'API (FastAPI + Uvicorn)
python apps/server/main.py
# → http://127.0.0.1:8080/healthz
```

## Docker Compose (Pi5 / Worker)
```bash
# Pi5
docker compose -f infra/compose/compose.pi.yml up -d

# Worker
docker compose -f infra/compose/compose.worker.yml up -d
```

## Endpoints utiles
- `GET /healthz` : état de l'API
- `POST /query` : (stub) requête RAG
- `POST /parliament/ask` : (stub) délibération multi-agents minimale
```json
{ "query": "question", "mode": "answer" }
```

## Backup Qdrant
```bash
bash infra/scripts/qdrant_snapshot.sh backup
bash infra/scripts/qdrant_snapshot.sh restore 2025-10-18T00-00-00Z
```

---
> ⚠️ MVP: RAG/Agents sont des squelettes avec logique simplifiée pour démarrer vite.
