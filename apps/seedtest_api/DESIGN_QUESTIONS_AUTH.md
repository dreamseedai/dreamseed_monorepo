# 문항 관리 API — 인증/권한 및 멀티테넌트 설계

본 문서는 SeedTest Question Bank(문항 관리) 백엔드의 인증/권한 및 멀티테넌트(조직 단위) 정책과 구현 가이드를 정리합니다. 목표는 다음과 같습니다.

- 요청 주체를 JWT로 인증하고 교사(teacher) 또는 관리자(admin)만 문항 API에 접근 가능
- 멀티테넌트: 교사는 자신의 조직(org_id)에 속한 문항만 생성/수정/삭제 가능
- 플랫폼 공용(글로벌) 문항은 기본적으로 교사 수정 금지, 필요 시 관리자만 수정 허용
- 보안·성능·운영을 고려한 데이터 모델 및 인덱스, 에러 처리, 테스트 전략 명세


## 신뢰 경계와 JWT 클레임

- 신뢰 경계: API는 "Authorization: Bearer <JWT>" 헤더의 JWT를 검증합니다.
- 요구 클레임(예):
  - `sub` (문자열, 사용자 식별자)
  - `roles` (리스트/스페이스 구분 문자열): `teacher`, `admin`, `student` 등
  - `org_id` (정수, 선택): 멀티테넌트 제어에 필요. 교사 권한에서 필수.
  - `scope` (선택): 세분화된 권한이 필요할 때 사용 가능 (예: `questions:read`, `questions:write`).
- 검증: RS256 + JWKS 또는 PEM 공개키, `iss`/`aud` 확인 (레포 내 security/jwt 사용).


## 역할/권한 규칙(요약)

- 학생(student): 문항 관리 API 접근 금지 → 403 Forbidden
- 교사(teacher): 자신의 조직(org_id)의 문항에 한해 읽기/생성/수정/삭제 허용
  - 조회: 자신의 org 문항 + 글로벌 문항 조회 허용
  - 수정/삭제: 기본은 자신의 org 문항만 허용
    - 예외: 글로벌 문항(org_id=NULL)이라도 해당 문항을 "본인이 생성"(created_by 또는 author == 본인)한 경우에 한해 수정/삭제 허용
- 관리자(admin): 기본적으로 제한 없음. 운영정책에 따라 글로벌 문항 편집 허용/금지 선택 가능

권한 판정은 "최소 권한" 원칙으로 구현합니다. 모호하면 거부(deny-by-default).


## 데이터 모델

- 테이블: `questions`
  - 컬럼 추가
    - `org_id INTEGER NULL` — 해당 문항 소유 조직. NULL이면 글로벌(공용)로 간주
    - `status TEXT NOT NULL DEFAULT 'draft'` — 기존 유지(draft|published|deleted)
  - 인덱스
    - `(org_id)` — 조직 스코프 필터
    - `(status)` — 상태 필터(이미 존재)
    - `(updated_at)` — 최신순 정렬 및 키셋 페이지네이션

- 글로벌(공용) 표기:
  - 권장: `org_id IS NULL`이면 글로벌로 취급
  - 대안: `PLATFORM_ORG_ID`(예: 0) 상수로 글로벌을 표현. 운영 환경과 합의 후 결정

마이그레이션(알렘빅):

```python
# apps/seedtest_api/alembic/versions/xxxx_questions_add_org_id.py
op.add_column('questions', sa.Column('org_id', sa.Integer(), nullable=True))
op.create_index('ix_questions_org_id', 'questions', ['org_id'])
```

기존 데이터 마이그레이션 전략:
- 운영 정책에 따라, 기존 문항을 모두 글로벌(NULL)로 두거나, 특정 org_id로 귀속
- "author='system'" 등 메타데이터로 글로벌 추정 시 NULL로 설정


## API 설계(핵심 엔드포인트)

- GET `/questions`
  - 교사: 자신 `org_id`의 문항만 조회. 글로벌 포함 여부는 요구사항에 따라 옵션(기본: 포함해서 보기만 가능, 수정 불가)
  - 관리자: org 스코프 제약 없음, `?org_id=...`로 필터 가능
  - 쿼리: 검색/정렬/페이지네이션(기존과 동일), 내부적으로 `WHERE (status!='deleted') AND (<role 조건>)`

- GET `/questions/{id}`
  - 교사: 자신의 org 문항 또는 글로벌 문항 조회 허용(수정은 별개 규칙)
  - 관리자: 제한 없음

- POST `/questions`
  - 교사: 토큰의 `org_id` 필수, 생성 시 `question.org_id = token.org_id`
  - 관리자: `org_id`를 바디에서 명시 허용 또는 생략 시 NULL(글로벌) 부여(운영정책 선택)
  - 응답: 생성된 문항

- PUT `/questions/{id}`
  - 교사: 다음 중 하나를 만족해야 허용
    1) 대상 문항의 `org_id == token.org_id`
    2) 대상 문항이 글로벌(`org_id IS NULL`)이며, `created_by` 또는 `author`가 JWT `sub`와 일치(해당 교사가 생성)
    - 그 외는 403(`forbidden_org` 또는 `forbidden_global`)
  - 관리자: 허용(운영정책에 따라 글로벌 편집 금지 시 `PLATFORM_GLOBAL_EDITABLE=false`이면 403)
  - 업데이트 시 `org_id` 변경 금지(403)

- DELETE `/questions/{id}`
  - 교사: 다음 중 하나를 만족해야 허용
    1) 대상 문항의 `org_id == token.org_id`
    2) 대상 문항이 글로벌(`org_id IS NULL`)이며, `created_by` 또는 `author`가 JWT `sub`와 일치(해당 교사가 생성)
    - 그 외는 403(`forbidden_org` 또는 `forbidden_global`)
  - 관리자: 허용(운영정책에 따라 글로벌 삭제 금지 시 `PLATFORM_GLOBAL_EDITABLE=false`이면 403)
  - 논리삭제(status='deleted') 유지


## 권한 체크(구현 가이드)

- 공통 디펜던시 재사용: `apps/seedtest_api/deps.py:get_current_user`
- 보조 헬퍼 추가 예시:

```python
# apps/seedtest_api/deps.py
from fastapi import HTTPException

def require_teacher_or_admin(user: User) -> None:
    if not (user.is_teacher() or user.is_admin()):
        raise HTTPException(403, 'forbidden')

def ensure_write_access_to_question(user: User, row) -> None:
    # row.org_id가 None이면 글로벌로 간주 → 교사 금지
  if user.is_teacher():
    row_org = getattr(row, 'org_id', None)
    if row_org is None:
      # 예외: 본인이 생성한 글로벌 문항은 허용
      created_by = getattr(row, 'created_by', None)
      author = getattr(row, 'author', None)
      if (created_by and str(created_by) == str(user.user_id)) or (author and str(author) == str(user.user_id)):
        return
      raise HTTPException(403, 'forbidden_global')
    if user.org_id is None or int(user.org_id) != int(row_org):
      raise HTTPException(403, 'forbidden_org')
    elif not user.is_admin():
        raise HTTPException(403, 'forbidden')
```

- 라우터 적용 예시(발췌):

```python
# apps/seedtest_api/routers/questions.py
@router.post('/questions')
def create_question(body: QuestionInput, current_user: User = Depends(get_current_user)):
    require_teacher_or_admin(current_user)
    if current_user.is_teacher():
        if current_user.org_id is None:
            raise HTTPException(403, 'missing_org')
        row.org_id = int(current_user.org_id)
    elif current_user.is_admin():
        # 관리자 정책: body.org_id를 허용하거나, None(글로벌)로 생성
        row.org_id = getattr(body, 'org_id', None)
    ...

@router.put('/questions/{question_id}')
@router.delete('/questions/{question_id}')
def modify_or_delete_question(...):
    row = s.get(QuestionRow, question_id)
    if row is None or row.status == 'deleted':
        raise HTTPException(404, 'not_found')
    ensure_write_access_to_question(current_user, row)
    # org_id 변경 금지
    ...
```

- 목록 조회에서의 역할별 필터:

```python
if current_user.is_teacher():
    if current_user.org_id is None:
        raise HTTPException(403, 'missing_org')
    where.append(QuestionRow.org_id == int(current_user.org_id))
    # 글로벌 포함만 허용하려면 OR 조건으로 포함하되 수정 금지는 별도 체크로 처리
elif current_user.is_admin():
    # optional: ?org_id 파라미터로 범위 제한
    if org_id_param is not None:
        where.append(QuestionRow.org_id == int(org_id_param))
else:
    raise HTTPException(403, 'forbidden')
```


## 에러 코드 표준화(권장)

- 401 unauthorized: 토큰 누락/유효하지 않음
- 403 forbidden: 역할 불충분(student 등)
- 403 forbidden_org: 교사이지만 다른 org 문항 수정/삭제 시도
- 403 forbidden_global: 교사가 글로벌 문항 수정/삭제 시도
- 403 missing_org: 교사 토큰에 org_id 누락
- 404 not_found: 문항 없음 또는 deleted
- 400 answer_out_of_range 등 유효성 오류


## 운영/설정 옵션

- `PLATFORM_GLOBAL_EDITABLE`(bool, 기본 false): 관리자의 글로벌 편집 허용 여부
- `DEFAULT_GLOBAL_ON_ADMIN_CREATE`(bool, 기본 true): 관리자가 org_id 미지정 생성 시 글로벌로 둘지 여부
- `BANK_ORG_ID`(int|None): 특정 org를 플랫폼 대표로 취급하고 싶을 경우

해당 옵션은 `apps/seedtest_api/settings.py`에 추가하여 환경변수로 제어합니다.


## 인덱싱/성능

- `ix_questions_org_id` 추가로 조직 필터 효율화
- 기존 `status`/`updated_at` 인덱스와 함께 keyset 페이지네이션 사용 권장
- 관리자 광범위 조회에는 추가 필터(기간/상태)를 강제하여 풀스캔 방지


## 테스트 전략

- JWT 역할/조직 조합 테스트
  - teacher(org=10) → org=10 문항 생성/수정/삭제 OK, org=20/글로벌 수정/삭제 403
  - admin → 기본 허용, 설정값에 따라 글로벌 편집 허용/금지 케이스 검증
  - student → 모든 문항 API 403
- 목록 권한 필터링
  - teacher(org=10)가 org=20 문항이 포함되지 않음을 확인
  - admin은 ?org_id 파라미터에 따라 범위 제약 확인
- 마이그레이션 회귀 테스트: 기존 문항이 정상 조회/수정 금지 정책에 따르는지 확인


## 단계별 도입 제안

1) 스키마 확장: Alembic으로 `questions.org_id` 추가 및 인덱스 생성
2) 모델 반영: `QuestionRow`에 `org_id` 컬럼 추가
3) 권한 가드 추가: `deps.py`에 보조 헬퍼 및 `routers/questions.py` 라우트에 적용
4) 설정 확장: 운영 옵션을 `settings.py`에 추가(기본 안전값)
5) 테스트 보강: JWT 역할/조직 케이스, 글로벌 금지 케이스 추가
6) 배포: 마이그레이션 → 앱 롤아웃 → 모니터링(403 증가 여부/오탐감지)

---

질문이나 정책 세부(글로벌 편집 허용 범위, 관리자 생성 시 기본 org 정책 등)를 확정해 주시면, 위 단계에 맞춰 코드/마이그레이션/테스트까지 바로 반영하겠습니다.
