#!/usr/bin/env bash
# EdgeVision SOC Launcher
set -e

PORT=${PORT:-8080}
NVIDIA_LLM_URL=${NVIDIA_LLM_URL:-"http://localhost:11434"}

echo "=========================================================="
echo "🚀 Starting EdgeVision // NVIDIA AI Cluster SOC"
echo "🌐 URL: http://localhost:${PORT}"
echo "=========================================================="

# Try opening the browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  (sleep 1.2 && open "http://localhost:${PORT}") &
fi

python3 server.py
