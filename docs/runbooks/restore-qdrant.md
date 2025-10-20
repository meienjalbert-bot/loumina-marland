# Restore Qdrant (runbook)

1) Arrêter le service:
```bash
systemctl --user stop loumina-parliament.service
```

2) Restaurer:
```bash
bash infra/scripts/qdrant_snapshot.sh restore 2025-10-18T00-00-00Z
```

3) Redémarrer:
```bash
systemctl --user start loumina-parliament.service
```
