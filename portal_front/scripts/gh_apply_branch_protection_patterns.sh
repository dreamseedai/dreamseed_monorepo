#!/usr/bin/env bash
# Apply branch protection and required status checks to patterns
# - Supports exact branches (e.g., "main") and prefix patterns (e.g., "release/", "feature/")
# - Supports exclusion patterns via regex/glob-like input ("*" is treated as ".*")
# - Supports parallel application with xargs -P
# - Can read defaults from a JSON config file
# Requires: gh CLI admin access; jq
#
# Usage:
#   ./scripts/gh_apply_branch_protection_patterns.sh <owner> <repo> "check1,check2,check3" [options]
#   ./scripts/gh_apply_branch_protection_patterns.sh --config path/to/branch_protection.config.json [options]
#
# Options:
#   --patterns "main,release/,feature/"   Comma-separated list of patterns. "default" targets the repository default branch.
#   --exclude  "feature/wip-*,temp/.*"    Comma-separated exclude patterns (glob-like: * becomes .*)
#   --parallel N                          Apply protections in parallel (default 2)
#   --reviews N                           Required approving review count (default 1)
#   --enforce-admins true|false           Enforce admins (default true)
#   --strict true|false                   Require status checks to be up to date before merging (default true)
#   --dry-run                             Print actions without applying changes
#   --config PATH                         Read defaults from JSON (see sample file)
set -euo pipefail

OWNER=""; REPO=""; CHECKS_CSV=""
CONFIG_PATH="${BRANCH_PROTECTION_CONFIG_JSON:-}"
PATTERNS_CSV=""
EXCLUDE_CSV=""
PARALLEL=2
REQUIRED_REVIEWS=1
ENFORCE_ADMINS=true
STRICT_CHECKS=true
DRY_RUN=false

# Positional or config-based inputs
if [[ $# -ge 3 && "${1:0:2}" != "--" ]]; then
  OWNER="$1"; shift
  REPO="$1"; shift
  CHECKS_CSV="$1"; shift
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --patterns)
      PATTERNS_CSV="$2"; shift 2 ;;
    --exclude)
      EXCLUDE_CSV="$2"; shift 2 ;;
    --parallel)
      PARALLEL="$2"; shift 2 ;;
    --reviews)
      REQUIRED_REVIEWS="$2"; shift 2 ;;
    --enforce-admins)
      ENFORCE_ADMINS="$2"; shift 2 ;;
    --strict)
      STRICT_CHECKS="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --config)
      CONFIG_PATH="$2"; shift 2 ;;
    *)
      echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2; exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required" >&2; exit 1
fi

# Load config if provided
if [[ -n "$CONFIG_PATH" && -f "$CONFIG_PATH" ]]; then
  # Only fill values not provided on CLI
  OWNER=${OWNER:-$(jq -r '.owner // empty' "$CONFIG_PATH")}
  REPO=${REPO:-$(jq -r '.repo // empty' "$CONFIG_PATH")}
  if [[ -z "$CHECKS_CSV" ]]; then
    CHECKS_CSV=$(jq -r '[.required_checks[]] | join(",")' "$CONFIG_PATH" 2>/dev/null || echo "")
  fi
  if [[ -z "$PATTERNS_CSV" ]]; then
    PATTERNS_CSV=$(jq -r '[.patterns[]] | join(",")' "$CONFIG_PATH" 2>/dev/null || echo "")
  fi
  if [[ -z "$EXCLUDE_CSV" ]]; then
    EXCLUDE_CSV=$(jq -r '[.exclude[]] | join(",")' "$CONFIG_PATH" 2>/dev/null || echo "")
  fi
  # Overwrite only if not set by CLI; numeric/bool fallbacks handled below
  cfg_parallel=$(jq -r '.parallel // empty' "$CONFIG_PATH" 2>/dev/null || echo "")
  cfg_reviews=$(jq -r '.reviews // empty' "$CONFIG_PATH" 2>/dev/null || echo "")
  cfg_enforce=$(jq -r '.enforce_admins // empty' "$CONFIG_PATH" 2>/dev/null || echo "")
  cfg_strict=$(jq -r '.strict // empty' "$CONFIG_PATH" 2>/dev/null || echo "")
  [[ -n "$cfg_parallel" ]] && PARALLEL="$cfg_parallel"
  [[ -n "$cfg_reviews" ]] && REQUIRED_REVIEWS="$cfg_reviews"
  [[ -n "$cfg_enforce" ]] && ENFORCE_ADMINS="$cfg_enforce"
  [[ -n "$cfg_strict" ]] && STRICT_CHECKS="$cfg_strict"
fi

if [[ -z "$OWNER" || -z "$REPO" || -z "$CHECKS_CSV" ]]; then
  echo "Usage: $0 <owner> <repo> <required_checks_csv> [--patterns \"main,release/,feature/\"] [--exclude \"regex1,regex2\"] [--parallel N] [--reviews N] [--enforce-admins true|false] [--strict true|false] [--dry-run] [--config PATH]"
  echo "Or:   $0 --config path/to/config.json [other options]"
  exit 1
fi

# Defaults for patterns
if [[ -z "$PATTERNS_CSV" ]]; then
  PATTERNS_CSV="default,release/,feature/"
fi

# For wildcard/prefix patterns, enumerate existing branches and apply protection.
# Note: GitHub API does not support wildcard protection directly; re-run periodically to apply to new branches.

UPDATER="$(dirname "$0")/gh_branch_protection_update.sh"
apply_protection() {
  local branch="$1"
  echo "Applying protection to $branch"
  if [[ "$DRY_RUN" == "true" ]]; then
    bash "$UPDATER" "$OWNER" "$REPO" "$branch" "$CHECKS_CSV" --reviews "$REQUIRED_REVIEWS" --enforce-admins "$ENFORCE_ADMINS" --strict "$STRICT_CHECKS" --dry-run || echo "[DRY-RUN] Failed (simulated) to apply to $branch" >&2
  else
    bash "$UPDATER" "$OWNER" "$REPO" "$branch" "$CHECKS_CSV" --reviews "$REQUIRED_REVIEWS" --enforce-admins "$ENFORCE_ADMINS" --strict "$STRICT_CHECKS" || echo "Failed to apply to $branch" >&2
  fi
}

# Determine default branch (fallback to main)
DEFAULT_BRANCH=$(gh repo view "$OWNER/$REPO" --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)

# Fetch all branches with pagination
BRANCH_JSON=$(gh api --paginate -H "Accept: application/vnd.github+json" "/repos/$OWNER/$REPO/branches?per_page=100" 2>/dev/null || true)
ALL_REMOTE_BRANCHES=()
if [[ -n "$BRANCH_JSON" ]]; then
  mapfile -t ALL_REMOTE_BRANCHES < <(echo "$BRANCH_JSON" | jq -r -s 'map(.[]?.name)[]')
fi

# Build candidate list from patterns
IFS=',' read -r -a PATTERNS <<< "$PATTERNS_CSV"
declare -a CANDIDATES=()
for pat in "${PATTERNS[@]}"; do
  pat="${pat## }"; pat="${pat%% }"
  [[ -z "$pat" ]] && continue
  if [[ "$pat" == "default" ]]; then
    CANDIDATES+=("$DEFAULT_BRANCH")
  elif [[ "$pat" == */ ]]; then
    if [[ ${#ALL_REMOTE_BRANCHES[@]} -gt 0 ]]; then
      for rb in "${ALL_REMOTE_BRANCHES[@]}"; do
        if [[ "$rb" == $pat* ]]; then
          CANDIDATES+=("$rb")
        fi
      done
    fi
  else
    CANDIDATES+=("$pat")
  fi
done

# Apply excludes
if [[ -n "$EXCLUDE_CSV" && ${#CANDIDATES[@]} -gt 0 ]]; then
  IFS=',' read -r -a EXCLUDES <<< "$EXCLUDE_CSV"
  REGEX_PARTS=()
  for ex in "${EXCLUDES[@]}"; do
    ex="${ex## }"; ex="${ex%% }"
    [[ -z "$ex" ]] && continue
    ex_regex="${ex//"*"/".*"}"
    REGEX_PARTS+=("$ex_regex")
  done
  if [[ ${#REGEX_PARTS[@]} -gt 0 ]]; then
    EX_RE="$(IFS='|'; echo "${REGEX_PARTS[*]}")"
    mapfile -t CANDIDATES < <(printf '%s\n' "${CANDIDATES[@]}" | grep -Ev "${EX_RE}" || true)
  fi
fi

# Deduplicate
if [[ ${#CANDIDATES[@]} -gt 0 ]]; then
  mapfile -t CANDIDATES < <(printf '%s\n' "${CANDIDATES[@]}" | sort -u)
fi

echo "Target branches (after patterns and excludes):"
printf '  %s\n' "${CANDIDATES[@]}"

# Parallel or sequential application
DRY_RUN_FLAG=""; [[ "$DRY_RUN" == "true" ]] && DRY_RUN_FLAG="--dry-run"

if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  echo "No branches matched the provided patterns." >&2
  exit 0
fi

export OWNER REPO CHECKS_CSV REQUIRED_REVIEWS ENFORCE_ADMINS STRICT_CHECKS DRY_RUN_FLAG UPDATER
printf '%s\n' "${CANDIDATES[@]}" | xargs -r -P "$PARALLEL" -I {} bash -c '
  set -euo pipefail
  BR="$1"
  if [[ -n "$DRY_RUN_FLAG" ]]; then
    bash "$UPDATER" "$OWNER" "$REPO" "$BR" "$CHECKS_CSV" --reviews "$REQUIRED_REVIEWS" --enforce-admins "$ENFORCE_ADMINS" --strict "$STRICT_CHECKS" "$DRY_RUN_FLAG"
  else
    bash "$UPDATER" "$OWNER" "$REPO" "$BR" "$CHECKS_CSV" --reviews "$REQUIRED_REVIEWS" --enforce-admins "$ENFORCE_ADMINS" --strict "$STRICT_CHECKS"
  fi
' _ {}

echo "Done."