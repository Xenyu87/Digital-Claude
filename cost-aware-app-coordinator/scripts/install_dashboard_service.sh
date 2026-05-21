#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-codex-skill-dashboard}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-3002}"
INTERVAL="${INTERVAL:-15}"
SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root on the LXC dev machine."
  exit 1
fi

mkdir -p "${SKILL_ROOT}/reports"
cat > "${SERVICE_FILE}" <<SERVICE
[Unit]
Description=Codex Skill Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=${SKILL_ROOT}
ExecStart=${PYTHON_BIN} ${SKILL_ROOT}/scripts/serve_dashboard.py --host ${HOST} --port ${PORT} --interval ${INTERVAL} --no-open
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"
systemctl restart "${SERVICE_NAME}.service"

echo "Installed ${SERVICE_NAME}.service"
echo "Dashboard: http://<LXC-IP>:${PORT}/reports/skill-dashboard.html"
echo "Local check: systemctl status ${SERVICE_NAME}.service"
