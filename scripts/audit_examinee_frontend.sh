#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

ROOT_DIR="$(pwd)"
YELLOW='\033[1;33m'; GREEN='\033[1;32m'; RED='\033[1;31m'; NC='\033[0m'

note() { echo -e "${YELLOW}== $* ==${NC}"; }
ok()   { echo -e "${GREEN}$*${NC}"; }
fail() { echo -e "${RED}$*${NC}"; }

# Require tools
command -v jq >/dev/null || { fail "jq is required"; exit 1; }
if ! command -v rg >/dev/null; then
  note "ripgrep (rg) not found; trying to install..."
  if command -v apt-get >/dev/null; then sudo apt-get update && sudo apt-get install -y ripgrep >/dev/null; fi
  command -v rg >/dev/null || { fail "ripgrep (rg) is required"; exit 1; }
fi

# A. Dependencies (next/react/tailwind/zustand/i18n)
note "Package deps"
DEPS_JSON=$(cat package.json 2>/dev/null || echo '{}')
MATCHES=$(echo "$DEPS_JSON" | jq -r '.dependencies, .devDependencies' 2>/dev/null | grep -E '"(next|react|tailwindcss|zustand|next-i18next|next-intl)"' || true)
if [[ -n "$MATCHES" ]]; then ok "$MATCHES"; else fail "deps not found (next/react/tailwind/zustand/i18n)"; fi

# Next.js i18n config
note "Next.js config i18n"
if rg -n --glob '!**/node_modules/**' 'i18n\s*:' next.config.* >/dev/null 2>&1; then ok "i18n config found"; else echo "i18n not found"; fi

# Tailwind config
note "Tailwind config"
if ls -1 tailwind.config.* 2>/dev/null | grep -E 'tailwind\.config\.(js|cjs|ts)$' >/dev/null; then ok "tailwind config present"; else echo "tailwind config missing"; fi

# B. Pages/Routes
note "Pages/Routes"
RG_EXAMS_IDX='pages/exams/index\.(tsx|jsx)|app/exams/page\.(tsx|jsx)'
RG_EXAMS_ID='pages/exams/\[examId\]\.(tsx|jsx)|app/exams/\[examId\]/page\.(tsx|jsx)'
RG_RESULT='pages/exams/\[examId\]/result\.(tsx|jsx)|app/exams/\[examId\]/result/page\.(tsx|jsx)'
rg -n --glob '!**/node_modules/**' -e "$RG_EXAMS_IDX" || echo "/exams not found"
rg -n --glob '!**/node_modules/**' -e "$RG_EXAMS_ID" || echo "/exams/[examId] not found"
rg -n --glob '!**/node_modules/**' -e "$RG_RESULT"     || echo "/exams/[examId]/result not found"

# C. Components
note "Components"
rg -n --glob '!**/node_modules/**' 'export default function ExamPage|const ExamPage' -S || echo "ExamPage not found"
rg -n --glob '!**/node_modules/**' 'QuestionCard' -S || echo "QuestionCard not found"
rg -n --glob '!**/node_modules/**' 'OptionList|OptionItem' -S || echo "OptionList/OptionItem not found"
rg -n --glob '!**/node_modules/**' 'Timer' -S || echo "Timer not found"
rg -n --glob '!**/node_modules/**' 'ProgressBar' -S || echo "ProgressBar not found"

# D. Zustand store / session persistence
note "Zustand store"
rg -n --glob '!**/node_modules/**' 'create\((set|.*)=>|create<|useExamStore' -S || echo "Zustand store/useExamStore not found"
rg -n --glob '!**/node_modules/**' 'sessionStorage|persist' -S || echo "session storage or persist not found"

# E. Auth guard (SSR/middleware)
note "Auth guard"
rg -n --glob '!**/node_modules/**' 'getServerSideProps|middleware\.(ts|js)|withAuth|getSession|getServerSession|next/navigation.*redirect\(' -S || echo "auth guard evidence not found"

# F. UX flow: API calls
note "API calls"
rg -n --glob '!**/node_modules/**' '/api/seedtest/exams|/api/seedtest/exams/.*/next|/api/seedtest/exams/.*/response' -S || echo "exam API calls not found"

ok "\nAudit finished. Review NOT FOUND lines (if any) for gaps."
