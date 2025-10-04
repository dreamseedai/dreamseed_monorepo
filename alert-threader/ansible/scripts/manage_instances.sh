#!/usr/bin/env bash
set -euo pipefail

ACTION=${1:?action (start|stop|restart|status|list|logs)}
INSTANCE_NAME=${2:-} # Optional for list/logs

case "$ACTION" in
  start)
    if [ -z "$INSTANCE_NAME" ]; then echo "Usage: $0 start <instance_name>"; exit 1; fi
    ./start_instance.sh "$INSTANCE_NAME"
    ;;
  stop)
    if [ -z "$INSTANCE_NAME" ]; then echo "Usage: $0 stop <instance_name>"; exit 1; fi
    ./stop_instance.sh "$INSTANCE_NAME"
    ;;
  restart)
    if [ -z "$INSTANCE_NAME" ]; then echo "Usage: $0 restart <instance_name>"; exit 1; fi
    ./restart_instance.sh "$INSTANCE_NAME"
    ;;
  status)
    if [ -z "$INSTANCE_NAME" ]; then echo "Usage: $0 status <instance_name>"; exit 1; fi
    ./status_instance.sh "$INSTANCE_NAME"
    ;;
  list)
    echo "Listing active Alert Threader instances:"
    systemctl list-units --type=service --state=running | grep "alert-threader@" || echo "No alert-threader instances running."
    ;;
  logs)
    if [ -z "$INSTANCE_NAME" ]; then echo "Usage: $0 logs <instance_name>"; exit 1; fi
    echo "Showing logs for alert-threader@$INSTANCE_NAME:"
    journalctl -u "alert-threader@$INSTANCE_NAME" -f --no-pager
    ;;
  *)
    echo "Unknown action: $ACTION"
    echo "Usage: $0 (start|stop|restart|status|list|logs) [instance_name]"
    exit 1
    ;;
esac