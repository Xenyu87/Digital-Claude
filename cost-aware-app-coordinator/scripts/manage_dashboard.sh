#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-codex-skill-dashboard}"
ACTION="${1:-status}"

case "${ACTION}" in
  start|stop|restart|status)
    systemctl "${ACTION}" "${SERVICE_NAME}.service"
    ;;
  logs)
    journalctl -u "${SERVICE_NAME}.service" -n 120 -f
    ;;
  test)
    python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test_all.py"
    ;;
  url)
    PORT="${PORT:-8765}"
    HOST_IP="$(hostname -I | awk '{print $1}')"
    echo "http://${HOST_IP}:${PORT}/reports/skill-dashboard.html"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|test|url}"
    exit 2
    ;;
esac
