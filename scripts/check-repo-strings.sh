#!/usr/bin/env bash
set -euo pipefail

# Repository rename legacy path checker
# This script checks for hardcoded references to old repository paths
# that should be updated after a repository rename.

echo "🔍 Checking for legacy repository path references..."

# Define patterns to check (add more as needed)
PATTERNS=(
    "mpcstudy/dreamseed"
    "mpcstudy/mpcstudy"
    "github.com/mpcstudy/dreamseed"
    "github.com/mpcstudy/mpcstudy"
)

FAIL=0
TOTAL_FOUND=0

for pattern in "${PATTERNS[@]}"; do
    echo "  Checking pattern: $pattern"
    
    # Search for pattern, excluding common directories
    if rg -n "$pattern" -S \
        --hidden \
        --glob '!node_modules/**' \
        --glob '!.git/**' \
        --glob '!.venv/**' \
        --glob '!venv/**' \
        --glob '!env/**' \
        --glob '!dist/**' \
        --glob '!build/**' \
        --glob '!coverage/**' \
        --glob '!.pytest_cache/**' \
        --glob '!__pycache__/**' \
        --glob '!.npm-cache/**' \
        --glob '!.cache/**' \
        >/dev/null 2>&1; then
        
        echo "❌ Found legacy repo path: $pattern"
        echo "   Files containing this pattern:"
        
        # Show first 10 matches with context
        rg -n "$pattern" -S \
            --hidden \
            --glob '!node_modules/**' \
            --glob '!.git/**' \
            --glob '!.venv/**' \
            --glob '!venv/**' \
            --glob '!env/**' \
            --glob '!dist/**' \
            --glob '!build/**' \
            --glob '!coverage/**' \
            --glob '!.pytest_cache/**' \
            --glob '!__pycache__/**' \
            --glob '!.npm-cache/**' \
            --glob '!.cache/**' \
            | sed -n '1,10p' | sed 's/^/     /'
        
        FAIL=1
        TOTAL_FOUND=$((TOTAL_FOUND + 1))
    else
        echo "  ✅ No matches found for: $pattern"
    fi
done

echo ""
if [ $FAIL -eq 1 ]; then
    echo "❌ Found $TOTAL_FOUND legacy repository path(s)."
    echo "   Please update these references to the new repository path."
    echo "   Current repository: mpcstudy/dreamseed_monorepo"
    echo ""
    echo "💡 Tip: Use 'rg -n \"<pattern>\" -S' to find and update these references."
    exit 1
else
    echo "✅ No legacy repository paths found."
    echo "   All references are up to date! 🎉"
    exit 0
fi
