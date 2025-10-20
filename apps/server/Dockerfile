FROM python:3.11-slim

WORKDIR /app

# Dépendances
COPY apps/server/requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends build-essential cmake \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /app/requirements.txt

# Code de l'API + agents
COPY apps/server /app/apps/server
COPY agents /app/agents

# --- Ajout: corpus du repo pour l'index BM25 ---
COPY README.md /app/README.md
COPY docs /app/docs
COPY rag /app/rag
COPY tests /app/tests
# (si tu veux limiter la taille de build, on peut exclure plus tard via .dockerignore)

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "apps.server.main"]
