#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [ -z "$ROOT_DIR" ]; then
  echo "Error: not inside a Git repository" >&2
  exit 1
fi

# Policy roots (conditionally run if present)
PF_POLICIES="$ROOT_DIR/portal_front/policies"
ROOT_POLICIES="$ROOT_DIR/policy/k8s"

if [ -d "$PF_POLICIES" ]; then
  echo "[opa-precommit] fmt/check: portal_front/policies"
  opa fmt -w "$PF_POLICIES"
  opa check "$PF_POLICIES"
fi

if [ -d "$ROOT_POLICIES" ]; then
  echo "[opa-precommit] fmt/check: policy/k8s"
  opa fmt -w "$ROOT_POLICIES"
  opa check "$ROOT_POLICIES"
fi

echo "[opa-precommit] done"
