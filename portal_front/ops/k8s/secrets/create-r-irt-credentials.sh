#!/bin/bash
# cSpell:ignore rirt
# Script to create r-irt-credentials Secret
#
# Usage:
#   # Interactive mode (prompts for token)
#   ./create-r-irt-credentials.sh
#
#   # With token as argument
#   ./create-r-irt-credentials.sh "your-token-here"
#
#   # Skip creation if token not needed
#   ./create-r-irt-credentials.sh --skip

set -euo pipefail

NAMESPACE="seedtest"
SECRET_NAME="r-irt-credentials"
TOKEN_KEY="token"

# Parse arguments
if [[ "${1:-}" == "--skip" ]]; then
    echo "[INFO] Skipping r-irt-credentials Secret creation"
    echo "[INFO] Note: R_IRT_INTERNAL_TOKEN is optional in CronJob configuration"
    exit 0
fi

TOKEN="${1:-}"

# Check if secret already exists
if kubectl -n "$NAMESPACE" get secret "$SECRET_NAME" &>/dev/null; then
    echo "[WARN] Secret $SECRET_NAME already exists in namespace $NAMESPACE"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Skipping. Use 'kubectl -n $NAMESPACE delete secret $SECRET_NAME' to delete first."
        exit 0
    fi
    echo "[INFO] Deleting existing secret..."
    kubectl -n "$NAMESPACE" delete secret "$SECRET_NAME"
fi

# Get token if not provided
if [[ -z "$TOKEN" ]]; then
    echo "[PROMPT] Enter R IRT Plumber internal token"
    echo "         (Leave empty if authentication is not required)"
    read -s -p "Token: " TOKEN
    echo
fi

# Create secret
if [[ -z "$TOKEN" ]]; then
    echo "[INFO] Token is empty. Creating secret with empty token (may cause issues if auth is required)"
    kubectl -n "$NAMESPACE" create secret generic "$SECRET_NAME" \
        --from-literal="$TOKEN_KEY"="" \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "[INFO] Creating secret $SECRET_NAME..."
    kubectl -n "$NAMESPACE" create secret generic "$SECRET_NAME" \
        --from-literal="$TOKEN_KEY"="$TOKEN"
fi

# Verify
echo "[INFO] Verifying secret creation..."
kubectl -n "$NAMESPACE" get secret "$SECRET_NAME"

echo ""
echo "✅ Secret created successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Verify secret: kubectl -n $NAMESPACE get secret $SECRET_NAME"
echo "   2. Check CronJob references: kubectl -n $NAMESPACE get cronjob calibrate-irt-weekly -o yaml | grep -A 5 R_IRT_INTERNAL_TOKEN"
echo "   3. Test calibration: kubectl -n $NAMESPACE create job --from=cronjob/calibrate-irt-weekly calibrate-irt-test-\$(date +%s)"

