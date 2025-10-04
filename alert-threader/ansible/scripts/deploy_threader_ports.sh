#!/usr/bin/env bash
set -euo pipefail

# =============================
# Alert Threader Port-based Deployment Script
# =============================

REPO_ROOT="$(dirname "$0")/.."
MODE=""
IMPL=""
PYTHON_PORT="9009"
NODE_PORT="9010"
GO_PORT="9011"
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
    --impl=python|node|go|multi  Threader implementation (default: multi)
    --python-port=PORT    Python service port (default: 9009)
    --node-port=PORT      Node.js service port (default: 9010)
    --go-port=PORT        Go service port (default: 9011)
    --test                 Run in test mode (check only)
    --verbose              Enable verbose output
    --help                 Show this help

Examples:
    $0 --impl=multi --python-port=9009 --node-port=9010 --go-port=9011
    $0 --mode=SOPS --impl=python --python-port=8009
    $0 --impl=multi --test --verbose
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
        --python-port=*)
            PYTHON_PORT="${arg#*=}"
            shift
            ;;
        --python-port)
            if [ -n "$2" ]; then
                PYTHON_PORT="$2"
                shift 2
            else
                echo "Error: --python-port requires an argument." >&2
                exit 1
            fi
            ;;
        --node-port=*)
            NODE_PORT="${arg#*=}"
            shift
            ;;
        --node-port)
            if [ -n "$2" ]; then
                NODE_PORT="$2"
                shift 2
            else
                echo "Error: --node-port requires an argument." >&2
                exit 1
            fi
            ;;
        --go-port=*)
            GO_PORT="${arg#*=}"
            shift
            ;;
        --go-port)
            if [ -n "$2" ]; then
                GO_PORT="$2"
                shift 2
            else
                echo "Error: --go-port requires an argument." >&2
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
    PLAYBOOK="playbooks/deploy_threader_ports.yaml"
    EXTRA_VARS="threader_mode=$MODE threader_impl=$IMPL threader_python_port=$PYTHON_PORT threader_node_port=$NODE_PORT threader_go_port=$GO_PORT"
elif [ -n "$MODE" ]; then
    # Only mode specified
    PLAYBOOK="playbooks/deploy_env.yaml"
    EXTRA_VARS="threader_mode=$MODE"
elif [ -n "$IMPL" ]; then
    # Only impl specified
    PLAYBOOK="playbooks/deploy_threader_ports.yaml"
    EXTRA_VARS="threader_impl=$IMPL threader_python_port=$PYTHON_PORT threader_node_port=$NODE_PORT threader_go_port=$GO_PORT"
else
    # Use defaults from group_vars
    PLAYBOOK="playbooks/deploy_threader_ports.yaml"
    EXTRA_VARS="threader_python_port=$PYTHON_PORT threader_node_port=$NODE_PORT threader_go_port=$GO_PORT"
fi

# =============================
# Execute Deployment
# =============================
echo "🚀 Starting Alert Threader port-based deployment..."
echo "Mode: ${MODE:-"from group_vars"}"
echo "Implementation: ${IMPL:-"multi"}"
echo "Python Port: $PYTHON_PORT"
echo "Node.js Port: $NODE_PORT"
echo "Go Port: $GO_PORT"
echo "Test Mode: $TEST_MODE"
echo "Verbose: $VERBOSE"
echo "Playbook: $PLAYBOOK"
echo "Extra Vars: $EXTRA_VARS"

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

echo "✅ Alert Threader port-based deployment completed successfully!"
echo ""
echo "Service endpoints:"
echo "  Python: http://localhost:$PYTHON_PORT/health"
echo "  Node.js: http://localhost:$NODE_PORT/health"
echo "  Go: http://localhost:$GO_PORT/health"
echo ""
echo "Test commands:"
echo "  curl http://localhost:$PYTHON_PORT/health"
echo "  curl http://localhost:$NODE_PORT/health"
echo "  curl http://localhost:$GO_PORT/health"
