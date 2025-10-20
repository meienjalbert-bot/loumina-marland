# ADR-0001 — Monorepo + SemVer + Trunk-Based

## Contexte
Projet solo, multi-modules (API, agents, RAG, infra). Besoin de simplicité.

## Décision
- Monorepo `loumina-marland/`.
- Trunk-based: branche `main` + branches courtes par feature.
- SemVer: tags `v0.1.0` à chaque incrément notable.

## Alternatives
- Multi-repos → plus de friction, synchro compliquée.

## Conséquences
- Déploiement simplifié (compose + Makefile).
- Historique Git centralisé, CI unique.
