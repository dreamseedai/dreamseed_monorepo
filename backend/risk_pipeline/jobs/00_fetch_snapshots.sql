-- 주간 리스크 리포트용 스냅샷 추출
-- 지난 14일간의 학습 로그, IRT 추정치, 출석 데이터

-- 키 정합성 및 인덱스 점검
-- 1) 필수 컬럼 존재 여부
SELECT column_name
FROM information_schema.columns
WHERE table_name IN ('fact_assessment','user_profile','org')
  AND column_name IN ('org_id','user_id','test_id','taken_at','theta_estimate','correct','omitted','attended')
ORDER BY table_name, column_name;

-- 2) 추천 인덱스
-- CREATE INDEX IF NOT EXISTS idx_fact_assessment_org_user_date ON fact_assessment(org_id, user_id, taken_at);

-- 3) 최근 14일 스냅샷 추출
\copy (
WITH recent_assessments AS (
  SELECT 
    org_id,
    user_id,
    test_id,
    taken_at::date AS assessment_date,
    theta_estimate,
    se_estimate,
    correct_count,
    incorrect_count,
    omitted_count,
    total_items,
    c_hat_estimate,
    duration_seconds
  FROM fact_assessment
  WHERE taken_at >= CURRENT_DATE - INTERVAL '14 days'
    AND taken_at < CURRENT_DATE
),

attendance_agg AS (
  SELECT
    org_id,
    student_id AS user_id,
    session_date::date AS attendance_date,
    CASE 
      WHEN status IN ('present', 'late') THEN 1
      ELSE 0
    END AS attended
  FROM attendance
  WHERE session_date >= CURRENT_DATE - INTERVAL '14 days'
    AND session_date < CURRENT_DATE
),

irt_snapshots AS (
  SELECT
    org_id,
    student_id AS user_id,
    week_start,
    theta,
    se,
    delta_theta,
    c_hat,
    omit_rate
  FROM irt_snapshot
  WHERE week_start >= CURRENT_DATE - INTERVAL '14 days'
),

combined AS (
  SELECT
    COALESCE(a.org_id, att.org_id, irt.org_id) AS org_id,
    COALESCE(a.user_id, att.user_id, irt.user_id) AS user_id,
    COALESCE(a.assessment_date, att.attendance_date, irt.week_start) AS record_date,
    a.test_id,
    a.theta_estimate,
    a.se_estimate,
    a.correct_count,
    a.incorrect_count,
    a.omitted_count,
    a.total_items,
    a.c_hat_estimate,
    a.duration_seconds,
    att.attended,
    irt.theta AS irt_theta,
    irt.se AS irt_se,
    irt.delta_theta AS irt_delta_theta,
    irt.c_hat AS irt_c_hat,
    irt.omit_rate AS irt_omit_rate
  FROM recent_assessments a
  FULL OUTER JOIN attendance_agg att 
    ON a.org_id = att.org_id 
    AND a.user_id = att.user_id 
    AND a.assessment_date = att.attendance_date
  FULL OUTER JOIN irt_snapshots irt
    ON COALESCE(a.org_id, att.org_id) = irt.org_id
    AND COALESCE(a.user_id, att.user_id) = irt.user_id
    AND DATE_TRUNC('week', COALESCE(a.assessment_date, att.attendance_date)) = irt.week_start
)

SELECT * FROM combined
ORDER BY org_id, user_id, record_date
) TO STDOUT WITH CSV HEADER;
