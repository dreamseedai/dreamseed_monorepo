"""
PostgreSQL problems 테이블 PRIMARY KEY를 UUID에서 MySQL ID(int)로 변경

주의: 이 작업은 외래 키를 재설정하므로 데이터베이스 다운타임이 필요합니다.
"""

PGPASSWORD = 'DreamSeedAi0908'

SQL_SCRIPT = """
-- ============================================================
-- PRIMARY KEY 변경: UUID → mysql_id_int
-- ============================================================

BEGIN;

-- 1. 기존 외래 키 제약 삭제
ALTER TABLE progress DROP CONSTRAINT IF EXISTS progress_problem_id_fkey;
ALTER TABLE submissions DROP CONSTRAINT IF EXISTS submissions_problem_id_fkey;

-- 2. 참조 테이블의 problem_id 타입 변경 준비
-- (현재 UUID → integer로 변경해야 함)

-- 2a. progress 테이블에 임시 컬럼 생성
ALTER TABLE progress ADD COLUMN problem_id_int INTEGER;

-- 2b. UUID → MySQL ID 매핑으로 데이터 복사
UPDATE progress p
SET problem_id_int = (
    SELECT mysql_id_int 
    FROM problems pr 
    WHERE pr.id = p.problem_id
);

-- 2c. submissions도 동일하게 처리
ALTER TABLE submissions ADD COLUMN problem_id_int INTEGER;

UPDATE submissions s
SET problem_id_int = (
    SELECT mysql_id_int 
    FROM problems pr 
    WHERE pr.id = s.problem_id
);

-- 3. problems 테이블 PRIMARY KEY 변경
ALTER TABLE problems DROP CONSTRAINT problems_pkey;
ALTER TABLE problems ADD PRIMARY KEY (mysql_id_int);

-- 4. 기존 UUID id 컬럼 삭제 (선택사항 - 백업용으로 남겨둘 수도 있음)
-- ALTER TABLE problems DROP COLUMN id;

-- 5. 참조 테이블의 problem_id 컬럼 교체
-- progress
ALTER TABLE progress DROP COLUMN problem_id;
ALTER TABLE progress RENAME COLUMN problem_id_int TO problem_id;
ALTER TABLE progress ALTER COLUMN problem_id SET NOT NULL;

-- submissions  
ALTER TABLE submissions DROP COLUMN problem_id;
ALTER TABLE submissions RENAME COLUMN problem_id_int TO problem_id;
ALTER TABLE submissions ALTER COLUMN problem_id SET NOT NULL;

-- 6. 외래 키 제약 재생성
ALTER TABLE progress 
ADD CONSTRAINT progress_problem_id_fkey 
FOREIGN KEY (problem_id) REFERENCES problems(mysql_id_int) ON DELETE CASCADE;

ALTER TABLE submissions 
ADD CONSTRAINT submissions_problem_id_fkey 
FOREIGN KEY (problem_id) REFERENCES problems(mysql_id_int) ON DELETE CASCADE;

-- 7. 인덱스 재생성
CREATE INDEX IF NOT EXISTS idx_progress_problem_id ON progress(problem_id);
CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions(problem_id);

COMMIT;

-- ============================================================
-- 검증 쿼리
-- ============================================================

-- problems 테이블 구조 확인
\d problems

-- 외래 키 확인
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE confrelid = 'problems'::regclass AND contype = 'f';

-- 데이터 샘플 확인
SELECT mysql_id_int, LEFT(title, 40) as title
FROM problems
WHERE mysql_id_int IN (1, 100, 1000)
ORDER BY mysql_id_int;
"""

if __name__ == "__main__":
    print("=" * 70)
    print("PostgreSQL PRIMARY KEY 변경 스크립트")
    print("=" * 70)
    print("\n⚠️  주의사항:")
    print("1. 이 작업은 외래 키를 재설정하므로 데이터베이스 다운타임이 필요합니다")
    print("2. 실행 전 데이터베이스 백업을 강력히 권장합니다")
    print("3. progress와 submissions에 데이터가 있으면 UUID→ID 매핑이 필요합니다")
    print("\n" + "=" * 70)
    
    response = input("\n계속하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("취소되었습니다.")
        exit(0)
    
    import subprocess
    
    # PostgreSQL 명령 실행
    process = subprocess.Popen(
        ['psql', '-U', 'postgres', '-h', '127.0.0.1', '-d', 'dreamseed'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={'PGPASSWORD': PGPASSWORD}
    )
    
    stdout, stderr = process.communicate(SQL_SCRIPT.encode())
    
    print("\n=== 실행 결과 ===")
    print(stdout.decode())
    
    if stderr:
        print("\n=== 에러 ===")
        print(stderr.decode())
    
    if process.returncode == 0:
        print("\n✅ PRIMARY KEY 변경 완료!")
    else:
        print("\n❌ 변경 실패")
        exit(1)
