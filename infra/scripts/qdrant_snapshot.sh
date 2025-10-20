#!/usr/bin/env bash
set -euo pipefail

CMD="${1:-}"
SNAPDIR="/srv/data/qdrant/snapshots"
DATE="$(date -u +%Y-%m-%dT%H-%M-%SZ)"

mkdir -p "$SNAPDIR"

case "$CMD" in
  backup)
    tar -czf "$SNAPDIR/qdrant-$DATE.tgz" -C /srv/data qdrant
    echo "Snapshot: $SNAPDIR/qdrant-$DATE.tgz"
    ;;
  restore)
    FILE="${2:-}"
    test -n "$FILE" || { echo "Usage: $0 restore <snapshot-file-or-stem>"; exit 1; }
    SRC="$FILE"
    if [[ ! -f "$SRC" ]]; then
      SRC="$SNAPDIR/$FILE.tgz"
    fi
    systemctl --user stop loumina-parliament.service 2>/dev/null || true
    tar -xzf "$SRC" -C /srv/data
    systemctl --user start loumina-parliament.service 2>/dev/null || true
    echo "Restored from $SRC"
    ;;
  *)
    echo "Usage: $0 backup|restore <file>"; exit 1;;
esac
