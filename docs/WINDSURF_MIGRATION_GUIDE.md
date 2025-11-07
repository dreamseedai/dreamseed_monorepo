# Windsurf 마이그레이션 가이드

## 배경

VS Code의 Copilot 채팅 패널은 **웹뷰(sandbox) 구조**로 인해 '전체 복사(One-click Copy All)'가 공식적으로 지원되지 않습니다.

### VS Code Copilot의 한계
- 포커스 복사/코드블록 단위 복사만 안정적으로 작동
- "대화 전체를 한 번에 복사"는 구조적으로 불가능
- 확장 프로그램으로도 포커스 복사까지만 보장

### Windsurf의 장점
- 응답·코드블록 단위 복사 버튼이 기본 제공
- Continue 기반으로 동일한 설정 사용 가능
- Copy Response 버튼 (하단 우측)으로 전체 복사 지원

---

## Windsurf로 빠르게 갈아타기

### 1) 모델/라우팅 설정 가져오기

기존 `~/.continue/config.yaml` 설정을 그대로 사용할 수 있습니다.
Windsurf도 Continue 기반이므로 동일 설정이 적용됩니다.

```bash
# 프로필 전환 (필요시)
~/init_ai_env.sh profile dev-fast      # 로컬 우선
~/init_ai_env.sh profile deep-reason   # 심층 추론(ko planning)
```

### 2) Windsurf에서 복사 UX 최적화

#### 기본 기능
- 응답 하단 우측: **Copy Response 버튼** (전체 복사)
- 코드 블록 우측 상단: **Copy 아이콘** (코드만 복사)

#### 권장 단축키 매핑

`Settings → Keyboard Shortcuts`에서 설정:

| 기능 | 권장 단축키 | 설명 |
|------|------------|------|
| 현재 패널 복사 | `Ctrl+Shift+C` (Linux/Win)<br>`Cmd+Shift+C` (Mac) | Cascade 응답 복사 |
| 모두 선택+복사 | `Ctrl+Alt+A` (Linux/Win)<br>`Cmd+Option+A` (Mac) | 에디터 전체 복사 |

설정 방법:
1. `Ctrl+K Ctrl+S` (Keyboard Shortcuts 열기)
2. "copy" 검색
3. 원하는 명령에 단축키 할당

### 3) VS Code를 계속 사용하는 경우

전체 복사는 포기하고, 다음 워크플로우 사용:

#### 옵션 A: 부분 복사
- **코드블록**: Copilot 자체 복사 버튼
- **일반 텍스트**: 포커스 복사 확장 사용
- **긴 응답**: "Insert into new file" → 에디터에서 `Ctrl+A` → 복사

#### 옵션 B: 우클릭 메뉴
- 응답 영역 우클릭 → "Copy"
- 코드 포함 여부는 버전에 따라 다름

⚠️ **주의**: Copilot의 웹뷰 특성상 "대화 전부"를 한 번에 긁는 확실한 API가 없습니다.

---

## 마이그레이션 체크리스트

### 필수 단계

- [ ] **Windsurf 설치**
  ```bash
  # 공식 사이트에서 다운로드
  # https://codeium.com/windsurf
  ```

- [ ] **Continue 설정 유지**
  - `~/.continue/config.yaml` 확인
  - GPT-5 / Sonnet 4.5 / 로컬 5090 라우팅 그대로 사용

- [ ] **첫 실행 후 설정 로드**
  - Windsurf 실행
  - `Continue: Reload Config` 명령 실행

- [ ] **단축키 매핑** (권장)
  - 패널 복사: `Ctrl+Shift+C`
  - 에디터 전체 복사: `Ctrl+Alt+A`

- [ ] **프로필 전환 테스트** (선택)
  ```bash
  ~/init_ai_env.sh profile dev-fast
  ~/init_ai_env.sh profile deep-reason
  ```

### 선택 단계

- [ ] **Windsurf 전용 키바인딩 JSON 생성**
- [ ] **온보딩 가이드 작성** (스크린샷 포함)
- [ ] **팀 공유 문서 작성**

---

## 비교표

| 기능 | VS Code Copilot | Windsurf Cascade |
|------|----------------|------------------|
| 전체 복사 버튼 | ❌ 없음 (구조적 한계) | ✅ 하단 우측에 있음 |
| 코드블록 복사 | ✅ 블록별 버튼 | ✅ 블록별 버튼 |
| 우클릭 복사 | ⚠️ 제한적 | ✅ 완전 지원 |
| 단축키 복사 | ⚠️ 포커스 복사만 | ✅ 전체 복사 가능 |
| Continue 통합 | ❌ 별도 확장 | ✅ 기본 내장 |
| 모델 라우팅 | ⚠️ 제한적 | ✅ config.yaml 지원 |

---

## 트러블슈팅

### Windsurf에서 설정이 안 보여요
```bash
# Continue 설정 확인
ls -la ~/.continue/config.yaml

# Windsurf 재시작 후 설정 리로드
# Ctrl+Shift+P → "Continue: Reload Config"
```

### 단축키가 충돌해요
1. `Settings → Keyboard Shortcuts`
2. 충돌하는 명령 검색
3. 기존 단축키 제거 또는 변경

### 모델 전환이 안 돼요
```bash
# 프로필 확인
~/init_ai_env.sh profile

# 설정 재생성
~/init_ai_env.sh profile dev-fast
```

---

## 추가 리소스

- **Windsurf 공식 문서**: https://codeium.com/windsurf/docs
- **Continue 설정 가이드**: https://continue.dev/docs
- **내부 설정**: `~/.continue/config.yaml`
- **프로필 관리**: `~/init_ai_env.sh`

---

**문서 업데이트**: 2025-11-05  
**버전**: 1.0  
**작성자**: DreamSeed AI Team
