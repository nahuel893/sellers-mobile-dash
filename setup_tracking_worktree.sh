#!/usr/bin/env bash
# One-shot script para dejar lista la worktree `feature/preventista-tracking`.
# Symlinkea el venv de Python (no duplica ~300MB) y copia el .env con credenciales.
#
# Uso:   ./setup_tracking_worktree.sh
# Seguro de correr múltiples veces: los targets se borran antes de recrearse.
set -euo pipefail

SOURCE_DIR="/home/nahuel/projects/work/seller-mobile-dashboard"
WORKTREE_DIR="/home/nahuel/projects/work/sellers-mobile-dashboard-tracking"

# Sanity checks
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: source dir no existe: $SOURCE_DIR" >&2
    exit 1
fi
if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo "ERROR: worktree no existe en: $WORKTREE_DIR" >&2
    echo "Creala primero con:  git worktree add -b feature/preventista-tracking $WORKTREE_DIR feature/ventas-mapa" >&2
    exit 1
fi
if [[ ! -d "$SOURCE_DIR/backend/.venv" ]]; then
    echo "ERROR: venv no existe en $SOURCE_DIR/backend/.venv" >&2
    exit 1
fi
if [[ ! -f "$SOURCE_DIR/.env" ]]; then
    echo "ERROR: .env no existe en $SOURCE_DIR/.env" >&2
    exit 1
fi

echo "==> Symlinking venv"
rm -f "$WORKTREE_DIR/backend/.venv"
ln -s "$SOURCE_DIR/backend/.venv" "$WORKTREE_DIR/backend/.venv"

echo "==> Copying .env"
cp "$SOURCE_DIR/.env" "$WORKTREE_DIR/.env"

echo ""
echo "==> Resultado:"
ls -la "$WORKTREE_DIR/backend/.venv" "$WORKTREE_DIR/.env"

echo ""
echo "==> Worktree lista. Para trabajar ahí:"
echo "    cd $WORKTREE_DIR"
echo "    claude  # (o como inicies Claude Code)"
