<!-- FILE: webstr/dev.sh -->
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GH_TOKEN=${GH_TOKEN:-""}  # set before running or in your shell profile
uvicorn server:app --host 0.0.0.0 --port 7860 --reload