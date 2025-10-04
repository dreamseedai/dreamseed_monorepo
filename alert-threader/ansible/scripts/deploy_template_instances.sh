#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying Alert Threader template-based instances..."
ansible-playbook -i ../inventory/hosts.yaml ../playbooks/deploy_template_instances.yaml -vvv
echo "✅ Template-based instance deployment complete."