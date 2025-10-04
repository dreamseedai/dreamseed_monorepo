#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(dirname "$0")/../.." # Adjust to monorepo root
ANSIBLE_DIR="$REPO_ROOT/alert-threader/ansible"
INVENTORY="$ANSIBLE_DIR/inventory/hosts.yaml"

ACTION=${1:?action (health|canary|rolling|rollback|monitor|deploy|status|logs)}
shift # Remove action from arguments

case "$ACTION" in
  health)
    echo "Running health checks for all instances..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/test_threader.yaml" "$@"
    ;;
  canary)
    echo "Starting Canary deployment..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/deploy_canary.yaml" "$@"
    ;;
  rolling)
    echo "Starting Rolling Update deployment..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/rolling_update.yaml" "$@"
    ;;
  rollback)
    echo "Initiating Rollback..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/auto_rollback.yaml" "$@"
    ;;
  monitor)
    echo "Setting up monitoring stack..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/setup_monitoring.yaml" "$@"
    ;;
  deploy)
    echo "Deploying all threader services..."
    ansible-playbook -i "$INVENTORY" "$ANSIBLE_DIR/playbooks/deploy_template_instances.yaml" "$@"
    ;;
  status)
    echo "Checking status of all threader services..."
    "$ANSIBLE_DIR/scripts/manage_instances.sh" list
    ;;
  logs)
    if [ -z "$1" ]; then echo "Usage: $0 logs <instance_name>"; exit 1; fi
    "$ANSIBLE_DIR/scripts/manage_instances.sh" logs "$1"
    ;;
  *)
    echo "Unknown action: $ACTION"
    echo "Usage: $0 (health|canary|rolling|rollback|monitor|deploy|status|logs) [args...]"
    exit 1
    ;;
esac