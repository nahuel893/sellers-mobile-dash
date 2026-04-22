#!/usr/bin/env bash
# One-shot script para dejar lista la worktree `feature/ventas-mapa`.
# Symlinkea el venv y frontend/node_modules (no duplica ~500MB) y copia el .env.
#
# Uso:   ./setup_mapa_worktree.sh
# Idempotente — los targets se borran antes de recrearse.
set -euo pipefail

SOURCE_DIR="/home/nahuel/projects/work/seller-mobile-dashboard"
WORKTREE_DIR="/home/nahuel/projects/work/sellers-mobile-dashboard-mapa"

# Sanity checks
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: source dir no existe: $SOURCE_DIR" >&2
    exit 1
fi
if [[ ! -d "$WORKTREE_DIR" ]]; then
    echo "ERROR: worktree no existe en: $WORKTREE_DIR" >&2
    echo "Creala primero con:  git worktree add $WORKTREE_DIR feature/ventas-mapa" >&2
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

echo "==> Symlinking backend venv"
rm -f "$WORKTREE_DIR/backend/.venv"
ln -s "$SOURCE_DIR/backend/.venv" "$WORKTREE_DIR/backend/.venv"

if [[ -d "$SOURCE_DIR/frontend/node_modules" ]]; then
    echo "==> Symlinking frontend node_modules"
    rm -rf "$WORKTREE_DIR/frontend/node_modules"
    ln -s "$SOURCE_DIR/frontend/node_modules" "$WORKTREE_DIR/frontend/node_modules"
else
    echo "==> Skipping node_modules (no existe en source — correr 'npm install' si necesitás)"
fi

echo "==> Copying .env"
cp "$SOURCE_DIR/.env" "$WORKTREE_DIR/.env"

echo ""
echo "==> Resultado:"
ls -la "$WORKTREE_DIR/backend/.venv" "$WORKTREE_DIR/.env" 2>&1
[[ -L "$WORKTREE_DIR/frontend/node_modules" ]] && ls -la "$WORKTREE_DIR/frontend/node_modules" 2>&1

echo ""
echo "==> Worktree lista. Para trabajar ahí:"
echo "    cd $WORKTREE_DIR"
echo "    claude"
