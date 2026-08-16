#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"
echo "ORBITAL GUARD — starting API + UI on http://127.0.0.1:8000"
exec python3 -m uvicorn api_server:app --host 0.0.0.0 --port 8000
