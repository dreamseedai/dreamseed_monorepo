# Windsurf 빠른 시작 가이드 (1분)

## 🎯 핵심만 빠르게

### 1. 키바인딩 설정 (30초)

```bash
mkdir -p ~/.windsurf-server/data/User
cp /home/won/projects/dreamseed_monorepo/docs/windsurf-keybindings.jsonc \
   ~/.windsurf-server/data/User/keybindings.json
```

### 2. Windsurf 재시작 (10초)

```bash
pkill -9 windsurf
windsurf /home/won/projects/dreamseed_monorepo &
```

### 3. 테스트 (20초)

1. `Ctrl+Shift+Space` - Cascade 열기
2. "Hello" 입력 → Enter
3. 응답 받으면 `Ctrl+Shift+C` - 전체 복사 ✅

---

## 💡 기억할 단축키 3개

| 단축키 | 기능 |
|--------|------|
| `Ctrl+Shift+C` | **전체 복사** ⭐ |
| `Ctrl+Shift+Space` | Cascade 열기/닫기 |
| `Ctrl+P` | 파일 검색 |

---

## 📖 자세한 내용

- **온보딩 가이드**: `docs/WINDSURF_ONBOARDING.md`
- **마이그레이션**: `docs/WINDSURF_MIGRATION_GUIDE.md`
- **키바인딩**: `docs/windsurf-keybindings.jsonc`

---

**완료 시간**: 1분  
**다음 단계**: 실제 코드 생성 테스트 🚀
