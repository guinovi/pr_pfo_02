#!/usr/bin/env bash
# Script de inicio rápido en Linux/macOS
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    ./.venv/bin/python iniciar.py
elif [ -d "venv" ]; then
    ./venv/bin/python iniciar.py
else
    python3 iniciar.py
fi

