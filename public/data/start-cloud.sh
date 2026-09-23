#!/usr/bin/env bash
set -euo pipefail
export HF_HOME=/workspace/computer10/hf-cache
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DOWNLOAD_TIMEOUT=60
export TOKENIZERS_PARALLELISM=false
cd /workspace/computer10/code
python -m pip install --break-system-packages -r model-requirements.txt fastapi==0.115.12 uvicorn==0.34.3
python -u download.py --root /workspace/computer10
exec python -u server.py --root /workspace/computer10
