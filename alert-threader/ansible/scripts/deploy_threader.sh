#!/usr/bin/env bash
set -euo pipefail

# =============================
# Alert Threader Deployment Script
# =============================

REPO_ROOT="$(dirname "$0")/.."
MODE=""
IMPL=""
TEST_MODE="false"
VERBOSE="false"

# =============================
# Usage
# =============================
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --mode=SOPS|VAULT     Secret management mode (default: from group_vars)
    --impl=python|node|go|multi  Threader implementation (default: python)
    --test                 Run in test mode (check only)
    --verbose              Enable verbose output
    --help                 Show this help

Examples:
    $0 --mode=SOPS --impl=python
    $0 --mode=VAULT --impl=multi --test
    $0 --impl=node --verbose
EOF
}

# =============================
# Parse Arguments
# =============================
for arg in "$@"; do
    case $arg in
        --mode=*)
            MODE="${arg#*=}"
            shift
            ;;
        --mode)
            if [ -n "$2" ]; then
                MODE="$2"
                shift 2
            else
                echo "Error: --mode requires an argument." >&2
                exit 1
            fi
            ;;
        --impl=*)
            IMPL="${arg#*=}"
            shift
            ;;
        --impl)
            if [ -n "$2" ]; then
                IMPL="$2"
                shift 2
            else
                echo "Error: --impl requires an argument." >&2
                exit 1
            fi
            ;;
        --test)
            TEST_MODE="true"
            shift
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            usage
            exit 1
            ;;
    esac
done

# =============================
# Build Ansible Command
# =============================
ANSIBLE_CMD="ansible-playbook -i ./inventory/hosts.yaml"

if [ "$VERBOSE" = "true" ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD -vvv"
fi

if [ "$TEST_MODE" = "true" ]; then
    ANSIBLE_CMD="$ANSIBLE_CMD --check"
fi

# =============================
# Determine Playbook
# =============================
if [ -n "$MODE" ] && [ -n "$IMPL" ]; then
    # Both mode and impl specified
    PLAYBOOK="playbooks/deploy_threader.yaml"
    EXTRA_VARS="threader_mode=$MODE threader_impl=$IMPL"
elif [ -n "$MODE" ]; then
    # Only mode specified
    PLAYBOOK="playbooks/deploy_env.yaml"
    EXTRA_VARS="threader_mode=$MODE"
elif [ -n "$IMPL" ]; then
    # Only impl specified
    PLAYBOOK="playbooks/deploy_threader.yaml"
    EXTRA_VARS="threader_impl=$IMPL"
else
    # Use defaults from group_vars
    PLAYBOOK="playbooks/deploy_threader.yaml"
    EXTRA_VARS=""
fi

# =============================
# Execute Deployment
# =============================
echo "🚀 Starting Alert Threader deployment..."
echo "Mode: ${MODE:-"from group_vars"}"
echo "Implementation: ${IMPL:-"python"}"
echo "Test Mode: $TEST_MODE"
echo "Verbose: $VERBOSE"
echo "Playbook: $PLAYBOOK"
echo "Extra Vars: ${EXTRA_VARS:-"none"}"

cd "$REPO_ROOT"

if [ -n "$EXTRA_VARS" ]; then
    $ANSIBLE_CMD "$PLAYBOOK" --extra-vars "$EXTRA_VARS"
else
    $ANSIBLE_CMD "$PLAYBOOK"
fi

# =============================
# Run Tests
# =============================
if [ "$TEST_MODE" = "false" ]; then
    echo "Running post-deployment tests..."
    $ANSIBLE_CMD playbooks/test_threader.yaml
fi

echo "✅ Alert Threader deployment completed successfully!"
