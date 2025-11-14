#!/usr/bin/env bash
# Bulk create GitHub issues from CSV using gh CLI
# Requires: gh (authenticated), bash
# Usage: ./scripts/gh_issues_bulk.sh owner repo project_management/github_issues.csv [org project_number] [--create-branch] [--create-pr] [--draft] [--reviewers user1,user2] [--base main] [--dry-run] [--dry-run-projects]
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <owner> <repo> <csv_path> [org project_number]"
  exit 1
fi

OWNER="$1"
REPO="$2"
CSV_PATH="$3"
shift 3

# Optional org/project_number positionals
ORG="$OWNER"
PROJECT_NUMBER=""
if [[ $# -ge 1 && $1 != --* ]]; then
  ORG="$1"; shift 1
fi
if [[ $# -ge 1 && $1 != --* ]]; then
  PROJECT_NUMBER="$1"; shift 1
fi
PROJECT_URL=""
if [[ -n "$PROJECT_NUMBER" ]]; then
  PROJECT_URL="https://github.com/orgs/${ORG}/projects/${PROJECT_NUMBER}"
fi

# Remaining are flags

# Optional flags
CREATE_BRANCH=false
CREATE_PR=false
PR_DRAFT=false
REVIEWERS=""
BASE_BRANCH="${BASE_BRANCH:-main}"
DRY_RUN=false
DRY_RUN_PROJECTS=false
ENSURE_LABELS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --create-branch) CREATE_BRANCH=true; shift ;;
    --create-pr) CREATE_PR=true; shift ;;
    --draft) PR_DRAFT=true; shift ;;
    --reviewers) REVIEWERS="$2"; shift 2 ;;
    --base) BASE_BRANCH="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --dry-run-projects) DRY_RUN_PROJECTS=true; shift ;;
    --ensure-labels) ENSURE_LABELS=true; shift ;;
    *) echo "Unknown flag: $1" >&2; shift ;;
  esac
done

if [[ ! -f "$CSV_PATH" ]]; then
  echo "CSV not found: $CSV_PATH" >&2
  exit 1
fi

# CSV headers: id,title,assignees,labels,story_points,branch[,body][,reviewers][,priority_label][,iteration_title]
# - assignees can be semicolon-separated; labels are comma-separated
# - Robust CSV parsing via Python (supports multiline body). Fields are read by header names case-insensitively.

IFS=$'\n'
# Stream CSV rows as NUL-delimited JSON objects using Python to handle multiline fields
while IFS= read -r -d '' ROW_JSON; do
  # Normalize keys to lowercase for case-insensitive access
  ROW=$(printf '%s' "$ROW_JSON" | jq 'with_entries(.key |= ascii_downcase)')
  ID=$(printf '%s' "$ROW" | jq -r '.id // empty')
  TITLE=$(printf '%s' "$ROW" | jq -r '.title // empty')
  ASSIGNEES=$(printf '%s' "$ROW" | jq -r '.assignees // empty')
  LABELS=$(printf '%s' "$ROW" | jq -r '.labels // empty')
  STORY_POINTS=$(printf '%s' "$ROW" | jq -r '.story_points // empty')
  BRANCH=$(printf '%s' "$ROW" | jq -r '.branch // empty')
  BODY_COL=$(printf '%s' "$ROW" | jq -r '.body // empty')
  REVIEWERS_CSV=$(printf '%s' "$ROW" | jq -r '.reviewers // empty')
  PRIORITY_LABEL_CSV=$(printf '%s' "$ROW" | jq -r '.priority_label // empty')
  ITERATION_TITLE_CSV=$(printf '%s' "$ROW" | jq -r '.iteration_title // empty')

  # Build body from template minimal; detailed body can be updated later
  if [[ -n "$BODY_COL" ]]; then
    BODY="$BODY_COL"
  else
    BODY=$(cat <<EOF
Auto-generated issue for roadmap item $ID

Branch: $BRANCH
Story Points: $STORY_POINTS

Refer to .github/ISSUE_TEMPLATE/implementation_checklist.md for checklist.
EOF
)
  fi

  # Convert labels to multiple --label args
  LABEL_ARGS=()
  IFS=',' read -ra LABS <<< "$LABELS"
  for l in "${LABS[@]}"; do
    l_trim="${l#"${l%%[![:space:]]*}"}"  # trim leading whitespace
    l_trim="${l_trim%"${l_trim##*[![:space:]]}"}"  # trim trailing whitespace
    if [[ -n "$l_trim" ]]; then
      # Optionally ensure label exists in the repo with a default color
      if $ENSURE_LABELS && ! $DRY_RUN; then
        # Cache labels in an assoc array to avoid repeated API calls
        if [[ -z "${_LABEL_CACHE_INITIALIZED:-}" ]]; then
          declare -gA _LABEL_CACHE
          while IFS= read -r name; do _LABEL_CACHE["$name"]=1; done < <(gh label list --repo "$OWNER/$REPO" --limit 1000 --json name --jq '.[].name' 2>/dev/null || true)
          _LABEL_CACHE_INITIALIZED=1
        fi
        if [[ -z "${_LABEL_CACHE[$l_trim]:-}" ]]; then
          gh label create "$l_trim" --repo "$OWNER/$REPO" --color "777777" --description "auto-created by bulk script" 2>/dev/null || true
          _LABEL_CACHE["$l_trim"]=1
        fi
      fi
      LABEL_ARGS+=(--label "$l_trim")
    fi
  done

  # Convert assignees
  ASSIGNEE_ARGS=()
  IFS=';' read -ra ASG <<< "$ASSIGNEES"
  for a in "${ASG[@]}"; do
    a_trim="${a#"${a%%[![:space:]]*}"}"
    a_trim="${a_trim%"${a_trim##*[![:space:]]}"}"
    [[ -n "$a_trim" ]] && ASSIGNEE_ARGS+=(--assignee "$a_trim")
  done

  echo "Creating issue: [$ID] $TITLE"
  if $DRY_RUN; then
    echo "DRY-RUN: gh issue create --repo $OWNER/$REPO --title [$ID] $TITLE ..."
  else
    # Try create with labels+assignees; fallback tiers: drop assignees, then drop labels
    TMP_BODY_FILE=""
    BODY_ARG=()
    if [[ -n "$BODY" ]]; then
      TMP_BODY_FILE=$(mktemp)
      printf "%s" "$BODY" > "$TMP_BODY_FILE"
      BODY_ARG=(-F "$TMP_BODY_FILE")
    fi

    # Helper to try create once with current BODY_ARG and provided extra args
    _try_create() {
      gh issue create \
        --repo "$OWNER/$REPO" \
        --title "[$ID] $TITLE" \
        "${BODY_ARG[@]}" \
        "$@"
    }

    if ! _try_create "${LABEL_ARGS[@]}" "${ASSIGNEE_ARGS[@]}"; then
      # If using file body, fallback once to inline body string for broader gh compatibility
      if [[ -n "$TMP_BODY_FILE" ]]; then
        BODY_ARG=(--body "$BODY")
        if _try_create "${LABEL_ARGS[@]}" "${ASSIGNEE_ARGS[@]}"; then
          :
        else
          # Proceed with fallback tiers below using inline body
          if [[ ${#ASSIGNEE_ARGS[@]} -gt 0 ]]; then
            echo "Warning: issue creation failed, retrying without assignees" >&2
            if _try_create "${LABEL_ARGS[@]}"; then
              :
            else
              if [[ ${#LABEL_ARGS[@]} -gt 0 ]]; then
                echo "Warning: retry without labels and assignees" >&2
                _try_create || { echo "Error: issue creation failed" >&2; [[ -n "$TMP_BODY_FILE" ]] && rm -f "$TMP_BODY_FILE"; continue; }
              else
                echo "Error: issue creation failed" >&2; [[ -n "$TMP_BODY_FILE" ]] && rm -f "$TMP_BODY_FILE"; continue
              fi
            fi
          else
            # No assignees; try dropping labels if present
            if [[ ${#LABEL_ARGS[@]} -gt 0 ]]; then
              echo "Warning: issue creation failed, retrying without labels" >&2
              _try_create || { echo "Error: issue creation failed" >&2; [[ -n "$TMP_BODY_FILE" ]] && rm -f "$TMP_BODY_FILE"; continue; }
            else
              echo "Error: issue creation failed" >&2; [[ -n "$TMP_BODY_FILE" ]] && rm -f "$TMP_BODY_FILE"; continue
            fi
          fi
        fi
      else
        # No body provided; proceed with existing fallbacks
        if [[ ${#ASSIGNEE_ARGS[@]} -gt 0 ]]; then
          echo "Warning: issue creation failed, retrying without assignees" >&2
          if _try_create "${LABEL_ARGS[@]}"; then
            :
          else
            if [[ ${#LABEL_ARGS[@]} -gt 0 ]]; then
              echo "Warning: retry without labels and assignees" >&2
              _try_create || { echo "Error: issue creation failed" >&2; continue; }
            else
              echo "Error: issue creation failed" >&2; continue
            fi
          fi
        else
          if [[ ${#LABEL_ARGS[@]} -gt 0 ]]; then
            echo "Warning: issue creation failed, retrying without labels" >&2
            _try_create || { echo "Error: issue creation failed" >&2; continue; }
          else
            echo "Error: issue creation failed" >&2; continue
          fi
        fi
      fi
    fi
    [[ -n "$TMP_BODY_FILE" ]] && rm -f "$TMP_BODY_FILE"
  fi

  # Get created issue number (last created by current user with matching title)
  if $DRY_RUN; then
    NEW_NUM="0"
  else
    NEW_NUM=$(gh issue list --repo "$OWNER/$REPO" --search "[$ID] $TITLE in:title" --state open --json number,title --jq '.[0].number' 2>/dev/null || true)
  fi

  # Optionally add to Projects V2 and set Status/Story Points via helper script
  if [[ -n "$PROJECT_NUMBER" && -n "$NEW_NUM" ]]; then
    # Status mapping by env JSON or config file
    STATUS="Inbox"
    PRIORITY_LABEL=""
    ITERATION_TITLE=""
    STATUS_MAP_JSON="${PROJECT_STATUS_MAP_JSON:-}"
    if [[ -n "${PROJECT_CONFIG_JSON:-}" && -f "$PROJECT_CONFIG_JSON" ]]; then
        # Validate config schema minimally
        if jq -e '(
            (has("statusLabelMap") and (.statusLabelMap|type=="object")) and
            ((has("storyPointsLabelPrefix") | not) or (.storyPointsLabelPrefix|type=="string")) and
            ((has("priorityLabelMap") | not) or (.priorityLabelMap|type=="object")) and
            ((has("iterationFromLabelPrefix") | not) or (.iterationFromLabelPrefix|type=="string"))
          )' "$PROJECT_CONFIG_JSON" >/dev/null 2>&1; then
          STATUS_MAP_JSON=$(jq -r 'try .statusLabelMap // empty' "$PROJECT_CONFIG_JSON")
          # Allow config to override story points prefix
          cfg_prefix=$(jq -r 'try .storyPointsLabelPrefix // empty' "$PROJECT_CONFIG_JSON")
          if [[ -n "$cfg_prefix" ]]; then SP_PREFIX="$cfg_prefix"; fi
          # Priority mapping based on labels
          PRIORITY_MAP_JSON=$(jq -r 'try .priorityLabelMap // empty' "$PROJECT_CONFIG_JSON")
          # Iteration derive from label like iter:YYYYwWW
          ITER_LABEL_PREFIX=$(jq -r 'try .iterationFromLabelPrefix // empty' "$PROJECT_CONFIG_JSON")
        else
          echo "Warning: PROJECT_CONFIG_JSON failed schema validation; ignoring" >&2
        fi
      fi
    if [[ -n "$STATUS_MAP_JSON" ]] && command -v jq >/dev/null 2>&1; then
      # Find first label present in map
      mapfile -t KEYS < <(echo "$STATUS_MAP_JSON" | jq -r 'keys[]')
      for key in "${KEYS[@]}"; do
        if [[ ",$LABELS," == *",$key,"* ]]; then
          STATUS=$(echo "$STATUS_MAP_JSON" | jq -r --arg k "$key" '.[$k]')
          break
        fi
      done
    else
      case ",${LABELS}," in
        *,implementation,*) STATUS="In Progress" ;;
        *,blocked,*) STATUS="Blocked" ;;
      esac
    fi

    # Story points: CSV or parse from labels with prefix
    SP_VAL="$STORY_POINTS"
    if [[ -z "$SP_VAL" || "$SP_VAL" == "null" ]]; then
      SP_PREFIX="${STORY_POINTS_LABEL_PREFIX:-${SP_PREFIX:-sp:}}"
      # parse labels like sp:3
      IFS=',' read -ra LBS <<< "$LABELS"
      for lb in "${LBS[@]}"; do
        lb_trim="${lb#"${lb%%[![:space:]]*}"}"
        lb_trim="${lb_trim%"${lb_trim##*[![:space:]]}"}"
        if [[ "$lb_trim" == $SP_PREFIX* ]]; then
          SP_VAL=${lb_trim#${SP_PREFIX}}
          break
        fi
      done
    fi

    # Priority: CSV override > config map from labels > simple fallback
    if [[ -n "$PRIORITY_LABEL_CSV" && "$PRIORITY_LABEL_CSV" != "null" ]]; then
      PRIORITY_LABEL="$PRIORITY_LABEL_CSV"
    fi
    if [[ -n "${PRIORITY_MAP_JSON:-}" ]] && command -v jq >/dev/null 2>&1; then
      if [[ -z "$PRIORITY_LABEL" ]]; then
        mapfile -t P_KEYS < <(echo "$PRIORITY_MAP_JSON" | jq -r 'keys[]')
        for pk in "${P_KEYS[@]}"; do
          if [[ ",$LABELS," == *",$pk,"* ]]; then
            PRIORITY_LABEL=$(echo "$PRIORITY_MAP_JSON" | jq -r --arg k "$pk" '.[$k]')
            break
          fi
        done
      fi
    fi
    if [[ -z "$PRIORITY_LABEL" ]]; then
      case ",${LABELS}," in
        *,p1,*) PRIORITY_LABEL="P1" ;;
        *,p2,*) PRIORITY_LABEL="P2" ;;
      esac
    fi

    # Iteration: derive from label prefix, e.g., iter:2025w01 maps to iteration title "2025w01"
    # Iteration: CSV override > derive from label prefix
    if [[ -n "$ITERATION_TITLE_CSV" && "$ITERATION_TITLE_CSV" != "null" ]]; then
      ITERATION_TITLE="$ITERATION_TITLE_CSV"
    elif [[ -n "${ITER_LABEL_PREFIX:-}" ]]; then
      IFS=',' read -ra LBS2 <<< "$LABELS"
      for lb2 in "${LBS2[@]}"; do
        lb2_trim="${lb2#"${lb2%%[![:space:]]*}"}"
        lb2_trim="${lb2_trim%"${lb2_trim##*[![:space:]]}"}"
        if [[ "$lb2_trim" == ${ITER_LABEL_PREFIX}* ]]; then
          ITERATION_TITLE=${lb2_trim#${ITER_LABEL_PREFIX}}
          break
        fi
      done
    fi

    echo "Project intent: org=$ORG number=$PROJECT_NUMBER issue=#$NEW_NUM status=$STATUS sp=${SP_VAL:-0} priority=${PRIORITY_LABEL:-} iter=${ITERATION_TITLE:-}"
    if $DRY_RUN_PROJECTS; then
      echo "DRY-RUN-PROJECTS: would update project fields and comment with $PROJECT_URL"
    else
  $DRY_RUN || bash "$(dirname "$0")/gh_project_update.sh" "$ORG" "$PROJECT_NUMBER" "$NEW_NUM" "$STATUS" "${SP_VAL:-0}" "${PRIORITY_LABEL:-}" "${ITERATION_TITLE:-}" --repo-owner "$OWNER" --repo-name "$REPO" || echo "Project update skipped (error)" >&2
      # Comment on the issue to link the project
      if [[ -n "$PROJECT_URL" ]]; then
        $DRY_RUN && echo "DRY-RUN: gh issue comment #$NEW_NUM link to $PROJECT_URL" || gh issue comment --repo "$OWNER/$REPO" "$NEW_NUM" --body "Added to Project: $PROJECT_URL" || true
      fi
    fi
  fi

  # Optional: branch and PR
  if $CREATE_BRANCH; then
    if [[ -n "$BRANCH" && "$BRANCH" != "null" ]]; then
      if $DRY_RUN; then
        echo "DRY-RUN: git checkout -B $BRANCH $BASE_BRANCH && git push -u origin $BRANCH"
      else
        git fetch origin || true
        # Create local branch from base
        git checkout -B "$BRANCH" "$BASE_BRANCH" || true
        # Try push; if it fails because branch exists remotely, try to set upstream and continue
        if ! git push -u origin "$BRANCH"; then
          # If remote branch exists, set upstream and continue
          if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
            git branch --set-upstream-to "origin/$BRANCH" "$BRANCH" || true
          else
            echo "Warning: failed to push branch '$BRANCH' to origin." >&2
          fi
        fi
      fi
      if $CREATE_PR; then
        # If no reviewers provided, attempt CODEOWNERS wildcard fallback
        if [[ -z "$REVIEWERS" ]]; then
          repo_root=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
          codeowners_file=""
          if [[ -f "$repo_root/.github/CODEOWNERS" ]]; then codeowners_file="$repo_root/.github/CODEOWNERS"; fi
          if [[ -z "$codeowners_file" && -f "$repo_root/CODEOWNERS" ]]; then codeowners_file="$repo_root/CODEOWNERS"; fi
          if [[ -n "$codeowners_file" ]]; then
            owners=$( { grep -E '^\s*\*' "$codeowners_file" | tail -n1 | grep -o '@[A-Za-z0-9_.-]+' | tr '\n' ',' | sed 's/,$//'; } 2>/dev/null || true )
            if [[ -n "$owners" ]]; then REVIEWERS="$owners"; fi
          fi
        fi
        PR_TITLE="[$ID] $TITLE"
        # Build PR body from template + project link + closes
        REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
        PR_TEMPLATE=""
        if [[ -f "$REPO_ROOT/.github/PULL_REQUEST_TEMPLATE.md" ]]; then
          PR_TEMPLATE=$(cat "$REPO_ROOT/.github/PULL_REQUEST_TEMPLATE.md")
        fi
        PR_BODY="$PR_TEMPLATE\n\nCloses #$NEW_NUM"
        if [[ -n "$PROJECT_URL" ]]; then PR_BODY="$PR_BODY\n\nLinked Project: $PROJECT_URL"; fi
        PR_ARGS=(--repo "$OWNER/$REPO" --head "$BRANCH" --base "$BASE_BRANCH" --title "$PR_TITLE" --body "$PR_BODY")
        if $PR_DRAFT; then PR_ARGS+=(--draft); fi
        # Determine reviewers: merge CSV and --reviewers flag; support comma/semicolon split and dedupe
        COMBINED_REVIEWERS=""
        [[ -n "$REVIEWERS" ]] && COMBINED_REVIEWERS="$REVIEWERS"
        if [[ -n "$REVIEWERS_CSV" && "$REVIEWERS_CSV" != "null" ]]; then
          if [[ -n "$COMBINED_REVIEWERS" ]]; then COMBINED_REVIEWERS+="","$REVIEWERS_CSV"; else COMBINED_REVIEWERS="$REVIEWERS_CSV"; fi
        fi
        if [[ -n "$COMBINED_REVIEWERS" ]]; then
          declare -A rv_seen
          IFS=',' read -ra RVS <<< "${COMBINED_REVIEWERS//;/,}"
          for rv in "${RVS[@]}"; do
            rv_trim="${rv#"${rv%%[![:space:]]*}"}"
            rv_trim="${rv_trim%"${rv_trim##*[![:space:]]}"}"
            [[ -z "$rv_trim" ]] && continue
            if [[ -z "${rv_seen[$rv_trim]:-}" ]]; then
              PR_ARGS+=(--reviewer "$rv_trim")
              rv_seen[$rv_trim]=1
            fi
          done
          unset rv_seen
        fi
        if $DRY_RUN; then
          echo "DRY-RUN: gh pr create ${PR_ARGS[*]}"
        else
          gh pr create "${PR_ARGS[@]}" || true
        fi
        # Link project in PR comments
        if [[ -n "$PROJECT_URL" && $DRY_RUN_PROJECTS == false ]]; then
          PR_NUM=$(gh pr view --repo "$OWNER/$REPO" --head "$BRANCH" --json number --jq '.number' 2>/dev/null || true)
          if [[ -n "$PR_NUM" ]]; then
            $DRY_RUN && echo "DRY-RUN: gh pr comment #$PR_NUM link to $PROJECT_URL" || gh pr comment --repo "$OWNER/$REPO" "$PR_NUM" --body "Linked Project: $PROJECT_URL" || true
          fi
        fi
      fi
    fi
  fi

done < <(python3 - "$CSV_PATH" <<'PY'
import sys,csv,json
from pathlib import Path
fp = Path(sys.argv[1])
with fp.open(newline='') as f:
  r = csv.DictReader(f)
  for row in r:
    sys.stdout.write(json.dumps(row, ensure_ascii=False))
    sys.stdout.write('\0')
PY
)

echo "Done."