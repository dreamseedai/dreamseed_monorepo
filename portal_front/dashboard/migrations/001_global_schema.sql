-- ============================================================================
-- DreamseedAI 글로벌 확장 데이터베이스 마이그레이션
-- 버전: 001
-- 작성일: 2025-11-06
-- 목적: 다국가, 다과목, 다학년, 다교육 형태 지원을 위한 스키마 확장
-- ============================================================================

-- ============================================================================
-- 1. 과목 마스터 테이블 (신규 생성)
-- ============================================================================

CREATE TABLE IF NOT EXISTS subjects_master (
  subject_code VARCHAR(20) PRIMARY KEY,
  subject_name_en VARCHAR(100) NOT NULL,
  subject_name_ko VARCHAR(100),
  subject_name_zh VARCHAR(100),
  subject_name_ja VARCHAR(100),
  subject_name_es VARCHAR(100),
  
  -- 과목 분류
  category VARCHAR(50) NOT NULL,           -- 'math', 'science', 'language', 'social', 'cs'
  subcategory VARCHAR(50),                 -- 'algebra', 'mechanics', 'organic', 'molecular'
  
  -- 난이도/레벨
  min_grade VARCHAR(10),                   -- 'G9', 'Year10', '중1'
  max_grade VARCHAR(10),                   -- 'G12', 'Year13', '고3'
  difficulty_level INT CHECK (difficulty_level BETWEEN 1 AND 5),
  
  -- 지원 국가/커리큘럼
  supported_countries TEXT[],              -- ['USA', 'CAN', 'GBR', 'AUS', 'KOR']
  supported_curricula TEXT[],              -- ['US-Common-Core', 'AP', 'IB', 'UK-GCSE']
  
  -- 상태
  is_active BOOLEAN DEFAULT TRUE,
  launch_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subjects_category ON subjects_master(category, is_active);
CREATE INDEX idx_subjects_country ON subjects_master USING GIN(supported_countries);

COMMENT ON TABLE subjects_master IS '글로벌 과목 마스터 테이블 - 모든 지원 과목의 메타데이터';

-- ============================================================================
-- 2. 조직 메타데이터 테이블 (신규 생성)
-- ============================================================================

CREATE TABLE IF NOT EXISTS organizations (
  org_id VARCHAR(50) PRIMARY KEY,
  org_name VARCHAR(200) NOT NULL,
  
  -- 조직 유형
  org_type VARCHAR(20) NOT NULL,           -- 'tutoring_center', 'private_academy', 'public_school', 'individual_tutor'
  education_type VARCHAR(20) NOT NULL,     -- 'tutoring', 'small_group', 'academy', 'public_school'
  
  -- 지역
  country VARCHAR(3) NOT NULL,             -- ISO 3166-1 alpha-3: 'USA', 'CAN', 'GBR', 'AUS', 'KOR', 'CHN'
  region VARCHAR(10),                      -- 'US-CA', 'US-NY', 'CA-ON', 'UK-LON', 'KR-SEL'
  city VARCHAR(100),
  timezone VARCHAR(50) NOT NULL,           -- 'America/Los_Angeles', 'Asia/Seoul'
  
  -- 규모
  student_capacity INT,
  teacher_count INT,
  
  -- 언어/커리큘럼
  primary_language VARCHAR(10) NOT NULL,   -- 'en-US', 'en-GB', 'ko-KR', 'zh-CN'
  supported_languages TEXT[],              -- ['en-US', 'ko-KR']
  curricula TEXT[],                        -- ['US-Common-Core', 'AP']
  
  -- 상태
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orgs_country_type ON organizations(country, org_type, is_active);
CREATE INDEX idx_orgs_education_type ON organizations(education_type, is_active);

COMMENT ON TABLE organizations IS '조직(학교/학원/개인교습소) 메타데이터';

-- ============================================================================
-- 3. 학생 테이블 확장 (기존 테이블에 컬럼 추가)
-- ============================================================================

-- 기존 students 테이블이 있다고 가정, 없으면 CREATE TABLE로 변경
DO $$
BEGIN
  -- 학년/학제 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='grade') THEN
    ALTER TABLE students ADD COLUMN grade VARCHAR(10);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='grade_system') THEN
    ALTER TABLE students ADD COLUMN grade_system VARCHAR(20);
  END IF;
  
  -- 지역/언어 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='region') THEN
    ALTER TABLE students ADD COLUMN region VARCHAR(10);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='country') THEN
    ALTER TABLE students ADD COLUMN country VARCHAR(3) DEFAULT 'USA';
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='language') THEN
    ALTER TABLE students ADD COLUMN language VARCHAR(10) DEFAULT 'en-US';
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='timezone') THEN
    ALTER TABLE students ADD COLUMN timezone VARCHAR(50) DEFAULT 'America/Los_Angeles';
  END IF;
  
  -- 교육 형태 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='education_type') THEN
    ALTER TABLE students ADD COLUMN education_type VARCHAR(20) DEFAULT 'tutoring';
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='group_size') THEN
    ALTER TABLE students ADD COLUMN group_size INT DEFAULT 1;
  END IF;
  
  -- 프라이버시 관련 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='date_of_birth') THEN
    ALTER TABLE students ADD COLUMN date_of_birth DATE;
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='parental_consent') THEN
    ALTER TABLE students ADD COLUMN parental_consent BOOLEAN DEFAULT FALSE;
  END IF;
  
  -- 활성 상태 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='is_active') THEN
    ALTER TABLE students ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='students' AND column_name='enrollment_date') THEN
    ALTER TABLE students ADD COLUMN enrollment_date DATE DEFAULT CURRENT_DATE;
  END IF;
END $$;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_students_grade_country ON students(grade, country);
CREATE INDEX IF NOT EXISTS idx_students_org_type ON students(org_id, education_type);
CREATE INDEX IF NOT EXISTS idx_students_country_active ON students(country, is_active);

COMMENT ON COLUMN students.grade IS '학년 (G9-G12, Year10-13, 중1-고3 등)';
COMMENT ON COLUMN students.country IS 'ISO 3166-1 alpha-3 국가 코드';
COMMENT ON COLUMN students.education_type IS '교육 형태: tutoring, small_group, academy, public_school';

-- ============================================================================
-- 4. 클래스 테이블 확장 (기존 테이블에 컬럼 추가)
-- ============================================================================

DO $$
BEGIN
  -- 과목 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='subject') THEN
    ALTER TABLE classes ADD COLUMN subject VARCHAR(50);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='subject_code') THEN
    ALTER TABLE classes ADD COLUMN subject_code VARCHAR(20);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='subject_level') THEN
    ALTER TABLE classes ADD COLUMN subject_level VARCHAR(20);
  END IF;
  
  -- 학년/국가 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='grade') THEN
    ALTER TABLE classes ADD COLUMN grade VARCHAR(10);
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='country') THEN
    ALTER TABLE classes ADD COLUMN country VARCHAR(3) DEFAULT 'USA';
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='curriculum') THEN
    ALTER TABLE classes ADD COLUMN curriculum VARCHAR(20);
  END IF;
  
  -- 교육 형태 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='education_type') THEN
    ALTER TABLE classes ADD COLUMN education_type VARCHAR(20) DEFAULT 'tutoring';
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='teacher_id') THEN
    ALTER TABLE classes ADD COLUMN teacher_id VARCHAR(50);
  END IF;
  
  -- 기간 컬럼
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='start_date') THEN
    ALTER TABLE classes ADD COLUMN start_date DATE;
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='end_date') THEN
    ALTER TABLE classes ADD COLUMN end_date DATE;
  END IF;
  
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name='classes' AND column_name='is_active') THEN
    ALTER TABLE classes ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
  END IF;
END $$;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_classes_subject_grade ON classes(subject, grade, country);
CREATE INDEX IF NOT EXISTS idx_classes_country_active ON classes(country, is_active);
CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id, is_active);

-- 외래키 추가 (subjects_master 참조)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                 WHERE constraint_name = 'fk_classes_subject_code') THEN
    ALTER TABLE classes ADD CONSTRAINT fk_classes_subject_code 
      FOREIGN KEY (subject_code) REFERENCES subjects_master(subject_code);
  END IF;
END $$;

COMMENT ON COLUMN classes.subject IS '과목명 (math, physics, chemistry, biology 등)';
COMMENT ON COLUMN classes.subject_level IS '난이도 (honors, AP, IB, regular, remedial)';
COMMENT ON COLUMN classes.curriculum IS '커리큘럼 (US-Common-Core, AP, IB, UK-GCSE 등)';

-- ============================================================================
-- 5. 초기 데이터: 과목 마스터
-- ============================================================================

INSERT INTO subjects_master (subject_code, subject_name_en, subject_name_ko, subject_name_zh, 
                              category, subcategory, min_grade, max_grade, difficulty_level,
                              supported_countries, supported_curricula, is_active, launch_date)
VALUES
  -- Math
  ('MATH-ALG1', 'Algebra 1', '대수학 1', '代数1', 'math', 'algebra', 'G9', 'G10', 2, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], TRUE, '2025-01-01'),
  ('MATH-ALG2', 'Algebra 2', '대수학 2', '代数2', 'math', 'algebra', 'G9', 'G11', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], TRUE, '2025-01-01'),
  ('MATH-GEOM', 'Geometry', '기하학', '几何', 'math', 'geometry', 'G9', 'G11', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], TRUE, '2025-01-01'),
  ('MATH-PRECALC', 'Pre-Calculus', '미적분 준비', '预备微积分', 'math', 'precalculus', 'G10', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], TRUE, '2025-01-01'),
  ('MATH-CALC-AB', 'Calculus AB', '미적분 AB', '微积分AB', 'math', 'calculus', 'G11', 'G12', 5, 
   ARRAY['USA','CAN'], ARRAY['AP'], TRUE, '2025-01-01'),
  ('MATH-CALC-BC', 'Calculus BC', '미적분 BC', '微积分BC', 'math', 'calculus', 'G11', 'G12', 5, 
   ARRAY['USA','CAN'], ARRAY['AP'], TRUE, '2025-01-01'),
  
  -- Physics
  ('PHYS-MECH', 'Mechanics', '역학', '力学', 'science', 'mechanics', 'G10', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-01-01'),
  ('PHYS-EM', 'Electromagnetism', '전자기학', '电磁学', 'science', 'electromagnetism', 'G11', 'G12', 5, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-01-01'),
  ('PHYS-THERMO', 'Thermodynamics', '열역학', '热力学', 'science', 'thermodynamics', 'G11', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-02-01'),
  ('PHYS-WAVES', 'Waves & Optics', '파동과 광학', '波动与光学', 'science', 'waves', 'G10', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-02-01'),
  
  -- Chemistry
  ('CHEM-GEN', 'General Chemistry', '일반화학', '普通化学', 'science', 'general', 'G10', 'G12', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP','IB'], TRUE, '2025-01-01'),
  ('CHEM-ORG', 'Organic Chemistry', '유기화학', '有机化学', 'science', 'organic', 'G11', 'G12', 5, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-03-01'),
  ('CHEM-INORG', 'Inorganic Chemistry', '무기화학', '无机化学', 'science', 'inorganic', 'G11', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-03-01'),
  
  -- Biology
  ('BIO-CELL', 'Cell Biology', '세포생물학', '细胞生物学', 'science', 'cell', 'G9', 'G11', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP','IB'], TRUE, '2025-01-01'),
  ('BIO-GENE', 'Genetics', '유전학', '遗传学', 'science', 'genetics', 'G10', 'G12', 4, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-01-01'),
  ('BIO-MOLEC', 'Molecular Biology', '분자생물학', '分子生物学', 'science', 'molecular', 'G11', 'G12', 5, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['AP','IB'], TRUE, '2025-02-01'),
  ('BIO-ECO', 'Ecology', '생태학', '生态学', 'science', 'ecology', 'G9', 'G11', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP','IB'], TRUE, '2025-02-01'),
  
  -- Future subjects (placeholder, not active yet)
  ('ENG-LIT', 'Literature', '문학', '文学', 'language', 'literature', 'G9', 'G12', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], FALSE, '2025-06-01'),
  ('SOC-HIST', 'World History', '세계사', '世界历史', 'social', 'history', 'G9', 'G12', 3, 
   ARRAY['USA','CAN','GBR','AUS'], ARRAY['US-Common-Core','AP'], FALSE, '2025-06-01'),
  ('CS-PYTHON', 'Python Programming', '파이썬 프로그래밍', 'Python编程', 'cs', 'programming', 'G9', 'G12', 3, 
   ARRAY['USA','CAN','GBR','AUS','KOR'], ARRAY['US-Common-Core','AP'], FALSE, '2025-07-01')
ON CONFLICT (subject_code) DO NOTHING;

-- ============================================================================
-- 6. 초기 데이터: 조직 샘플 (테스트용)
-- ============================================================================

INSERT INTO organizations (org_id, org_name, org_type, education_type, country, region, city, timezone,
                           student_capacity, teacher_count, primary_language, supported_languages, curricula, is_active)
VALUES
  ('ORG-USA-001', 'Silicon Valley Tutoring Center', 'tutoring_center', 'tutoring', 'USA', 'US-CA', 'San Francisco', 'America/Los_Angeles',
   100, 10, 'en-US', ARRAY['en-US','zh-CN'], ARRAY['US-Common-Core','AP'], TRUE),
  ('ORG-USA-002', 'Boston Academy of Sciences', 'private_academy', 'academy', 'USA', 'US-MA', 'Boston', 'America/New_York',
   500, 50, 'en-US', ARRAY['en-US'], ARRAY['US-Common-Core','AP','IB'], TRUE),
  ('ORG-CAN-001', 'Toronto Learning Center', 'tutoring_center', 'small_group', 'CAN', 'CA-ON', 'Toronto', 'America/Toronto',
   200, 20, 'en-CA', ARRAY['en-CA','fr-CA'], ARRAY['CAN-Provincial','AP'], TRUE),
  ('ORG-KOR-001', '서울과학학원', 'private_academy', 'academy', 'KOR', 'KR-SEL', 'Seoul', 'Asia/Seoul',
   1000, 100, 'ko-KR', ARRAY['ko-KR','en-US'], ARRAY['KR-National'], FALSE)  -- Not active yet
ON CONFLICT (org_id) DO NOTHING;

-- ============================================================================
-- 7. 기존 데이터 마이그레이션 (필요시 실행)
-- ============================================================================

-- 기존 students의 기본값 설정 (NULL인 경우만)
UPDATE students SET 
  country = 'USA',
  grade = 'G9',
  grade_system = 'US',
  language = 'en-US',
  timezone = 'America/Los_Angeles',
  education_type = 'tutoring',
  group_size = 1,
  is_active = TRUE
WHERE country IS NULL;

-- 기존 classes의 기본값 설정 (NULL인 경우만)
UPDATE classes SET 
  subject = 'math',
  subject_code = 'MATH-ALG2',
  country = 'USA',
  grade = 'G9',
  curriculum = 'US-Common-Core',
  education_type = 'tutoring',
  is_active = TRUE
WHERE country IS NULL;

-- ============================================================================
-- 8. 제약 조건 및 검증
-- ============================================================================

-- 국가 코드 검증
ALTER TABLE students ADD CONSTRAINT chk_students_country 
  CHECK (country ~ '^[A-Z]{3}$');

ALTER TABLE classes ADD CONSTRAINT chk_classes_country 
  CHECK (country ~ '^[A-Z]{3}$');

-- 학년 형식 검증 (G9-G12, Year10-13, 중1-고3 등)
ALTER TABLE students ADD CONSTRAINT chk_students_grade 
  CHECK (grade ~ '^(G[0-9]{1,2}|Year[0-9]{1,2}|[초중고][1-3])$');

ALTER TABLE classes ADD CONSTRAINT chk_classes_grade 
  CHECK (grade ~ '^(G[0-9]{1,2}|Year[0-9]{1,2}|[초중고][1-3])$');

-- 교육 형태 검증
ALTER TABLE students ADD CONSTRAINT chk_students_education_type 
  CHECK (education_type IN ('tutoring', 'small_group', 'academy', 'public_school'));

ALTER TABLE classes ADD CONSTRAINT chk_classes_education_type 
  CHECK (education_type IN ('tutoring', 'small_group', 'academy', 'public_school'));

-- ============================================================================
-- 9. 뷰 생성: 활성 학생 및 클래스
-- ============================================================================

CREATE OR REPLACE VIEW v_active_students_global AS
SELECT 
  s.student_id,
  s.student_name,
  s.org_id,
  s.class_id,
  s.grade,
  s.country,
  s.language,
  s.education_type,
  s.group_size,
  c.subject,
  c.subject_code,
  c.subject_level,
  c.curriculum,
  o.org_name,
  o.city,
  o.timezone
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN organizations o ON s.org_id = o.org_id
WHERE s.is_active = TRUE AND (c.is_active = TRUE OR c.is_active IS NULL);

COMMENT ON VIEW v_active_students_global IS '활성 학생 글로벌 뷰 - 조직/클래스 메타 조인';

-- ============================================================================
-- 10. 권한 설정 (필요시 수정)
-- ============================================================================

-- 읽기 전용 사용자
-- GRANT SELECT ON subjects_master, organizations, v_active_students_global TO readonly_user;

-- 일반 교사
-- GRANT SELECT ON students, classes, subjects_master TO teacher_user;
-- GRANT UPDATE (is_active, updated_at) ON students TO teacher_user;

-- 관리자
-- GRANT ALL PRIVILEGES ON students, classes, subjects_master, organizations TO admin_user;

-- ============================================================================
-- 마이그레이션 완료
-- ============================================================================

-- 버전 기록 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(20) PRIMARY KEY,
  description TEXT,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_migrations (version, description) 
VALUES ('001', 'Global expansion schema: countries, subjects, organizations')
ON CONFLICT (version) DO NOTHING;

SELECT 'Migration 001 completed successfully!' AS status;
