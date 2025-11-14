#!/usr/bin/env bash
# One-shot validation runner (dry-run first) for dreamseedai/dreamseed_monorepo
# Safe defaults: dry-runs only unless APPLY_* are set to true in the environment.
set -euo pipefail

# --- EDIT THESE VALUES IF NEEDED ---
ORG="dreamseedai"
REPO="dreamseed_monorepo"
PROJECT_NUMBER="${PROJECT_NUMBER:-1}"  # Override via env: export PROJECT_NUMBER=1
# Optional: project config JSON to customize label→field mapping
PROJECT_CONFIG_JSON_PATH="${PROJECT_CONFIG_JSON:-project_management/project_config.json}"

# Apply switches (override via env)
APPLY_ISSUES=${APPLY_ISSUES:-false}      # true to actually create issues from small CSV
APPLY_BP=${APPLY_BP:-false}              # true to actually apply branch protection
PARALLEL=${PARALLEL:-2}

# --- No edits below ---
ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCRIPTS_DIR="$ROOT_DIR/portal_front/scripts"
PM_DIR="$ROOT_DIR/portal_front/project_management"
CSV_FULL="$PM_DIR/github_issues.csv"
CSV_SMALL="$PM_DIR/github_issues_small.csv"
CSV_EXT_SAMPLE="$PM_DIR/github_issues_extended.sample.csv"
CSV_EXT_WORK="$PM_DIR/github_issues_extended.csv"

if ! command -v gh >/dev/null 2>&1; then echo "gh CLI required" >&2; exit 1; fi
if ! command -v jq >/dev/null 2>&1; then echo "jq required" >&2; exit 1; fi

# Show gh context
echo "== GH VERSION =="; gh --version || true
echo "== GH AUTH STATUS =="; gh auth status || true

# Optional project config
if [[ -n "$PROJECT_CONFIG_JSON_PATH" && -f "$PROJECT_CONFIG_JSON_PATH" ]]; then
  export PROJECT_CONFIG_JSON="$PROJECT_CONFIG_JSON_PATH"
  echo "Using PROJECT_CONFIG_JSON=$PROJECT_CONFIG_JSON"
fi

# 0) If extended sample exists, validate headers and use it preferentially
CSV_INPUT="$CSV_FULL"
if [[ -f "$CSV_EXT_SAMPLE" ]]; then
  echo "== EXTENDED SAMPLE DETECTED: $CSV_EXT_SAMPLE =="
  # Validate required headers in first line
  HEADER=$(head -n1 "$CSV_EXT_SAMPLE")
  python3 - "$HEADER" <<'PY' || { echo "Invalid extended CSV header" >&2; exit 1; }
import sys,csv
hdr = next(csv.reader([sys.argv[1]]))
req = {"id","title","assignees","labels","story_points","branch"}
missing = req.difference({h.strip().lower() for h in hdr})
assert not missing, f"Missing required cols: {sorted(missing)}"
PY
  cp "$CSV_EXT_SAMPLE" "$CSV_EXT_WORK"
  CSV_INPUT="$CSV_EXT_WORK"
fi

# 1) Dry-run bulk issues (no gh/git/project mutations)
if [[ -f "$CSV_INPUT" ]]; then
  echo "== DRY-RUN: bulk issues =="
  bash "$SCRIPTS_DIR/gh_issues_bulk.sh" "$ORG" "$REPO" "$CSV_INPUT" "$ORG" "$PROJECT_NUMBER" \
    --dry-run --dry-run-projects || true
else
  echo "WARNING: Missing $CSV_INPUT; skipping bulk issues dry-run"
fi

# 2) Small real run (first 2 rows)
if [[ -f "$CSV_INPUT" ]]; then
  echo "== SMALL CSV PREP =="
  head -n 3 "$CSV_INPUT" > "$CSV_SMALL"
  if [[ "${APPLY_ISSUES}" == "true" ]]; then
    echo "== REAL RUN (small) =="
    bash "$SCRIPTS_DIR/gh_issues_bulk.sh" "$ORG" "$REPO" "$CSV_SMALL" "$ORG" "$PROJECT_NUMBER"
  else
    echo "APPLY_ISSUES=false (skipping real issue creation)"
  fi
fi

# 3) Branch protection env mapping
echo "== BRANCH PROTECTION (dry-run) =="
bash "$SCRIPTS_DIR/gh_apply_branch_protection_env.sh" "$ORG" "$REPO" \
  --prod-checks "ci/build,ci/test,ci/deploy" \
  --staging-checks "ci/build,ci/test" \
  --base-checks "ci/lint" \
  --parallel "$PARALLEL" --dry-run

if [[ "${APPLY_BP}" == "true" ]]; then
  echo "== BRANCH PROTECTION (APPLY) =="
  bash "$SCRIPTS_DIR/gh_apply_branch_protection_env.sh" "$ORG" "$REPO" \
    --prod-checks "ci/build,ci/test,ci/deploy" \
    --staging-checks "ci/build,ci/test" \
    --base-checks "ci/lint" \
    --parallel "$PARALLEL"
else
  echo "APPLY_BP=false (skipping protection apply)"
fi

echo "Done. Review Actions logs and Project board fields, then fill in FINAL_CHECK_REPORT_TEMPLATE.md." 
