#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

# ── Detectar IP LAN ──────────────────────────────────────────────────────────
LAN_IP=$(ip route get 1 2>/dev/null | awk '{print $7; exit}')
if [[ -z "$LAN_IP" ]]; then
    LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi
if [[ -z "$LAN_IP" ]]; then
    LAN_IP="<ip-no-detectada>"
fi

# ── Limpiar procesos al salir ─────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "Deteniendo servicios..."
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID"
    fi
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID"
    fi
    wait
    echo "Listo."
}

trap cleanup INT TERM

# ── Regenerar cupos desde Excel ──────────────────────────────────────────────
echo "[cupos] Regenerando cupos.csv desde Excel..."
"$ROOT/backend/.venv/bin/python" "$ROOT/scripts/procesar_cupos.py" 2>&1 | \
    while IFS= read -r line; do echo "[cupos] $line"; done
echo "[cupos] Listo."
echo ""

# ── Levantar backend ──────────────────────────────────────────────────────────
(
    cd "$ROOT/backend"
    .venv/bin/uvicorn main:app --reload --port 8000 --host 0.0.0.0 2>&1 | \
        while IFS= read -r line; do echo "[backend] $line"; done
) &
BACKEND_PID=$!

# ── Levantar frontend ─────────────────────────────────────────────────────────
(
    cd "$ROOT/frontend"
    npm run dev -- --host 2>&1 | \
        while IFS= read -r line; do echo "[frontend] $line"; done
) &
FRONTEND_PID=$!

# ── URLs de acceso ────────────────────────────────────────────────────────────
echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│              Dev stack levantado                │"
echo "├──────────────┬──────────────────────────────────┤"
echo "│              │ Local                  LAN       │"
echo "├──────────────┼────────────────────────┬─────────┤"
echo "│ Frontend     │ http://localhost:5173  │ http://${LAN_IP}:5173  │"
echo "│ Backend      │ http://localhost:8000  │ http://${LAN_IP}:8000  │"
echo "│ API Docs     │ http://localhost:8000/docs        │"
echo "└──────────────┴────────────────────────────────────┘"
echo ""
echo "Backend PID: $BACKEND_PID  |  Frontend PID: $FRONTEND_PID"
echo "Presioná Ctrl+C para detener ambos procesos."
echo ""

# ── Mantener vivo hasta Ctrl+C ────────────────────────────────────────────────
wait
