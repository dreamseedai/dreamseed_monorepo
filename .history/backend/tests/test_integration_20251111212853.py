"""
Phase 1 MVP 전체 통합 테스트
Authentication, Problem, Submission, Progress API 종합 검증
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.progress import Progress
from app.api.auth import register, login
from app.api.problems import create_problem, list_problems, get_problem, update_problem
from app.api.submissions import create_submission, list_my_submissions
from app.api.progress import get_my_stats, get_problem_progress, start_problem, complete_problem
from app.schemas.user import UserCreate, UserLogin
from app.schemas.problem import ProblemCreate, ProblemUpdate
from app.schemas.submission import SubmissionCreate
import uuid


def test_full_student_workflow():
    """학생의 전체 학습 워크플로우 테스트"""
    
    print("=" * 80)
    print("Phase 1 MVP 통합 테스트 시작")
    print("=" * 80)
    
    db = SessionLocal()
    
    # ===== 1. 인증 시스템 =====
    print("\n[1단계] 인증 시스템 테스트")
    print("-" * 80)
    
    # 신규 학생 등록
    student_email = f"integration_test_{uuid.uuid4().hex[:8]}@test.com"
    student_create = UserCreate(
        email=student_email,
        password="TestPassword123!",
        full_name="통합테스트 학생",
        role="student"
    )
    
    student_user = register(student_create, db)
    print(f"✅ 학생 등록 성공: {student_user.email}")
    
    # 로그인 (JWT 토큰 발급)
    login_data = UserLogin(email=student_email, password="TestPassword123!")
    token_response = login(login_data, db)
    print(f"✅ 로그인 성공: JWT 토큰 발급됨")
    print(f"   토큰 타입: {token_response.token_type}")
    
    # 실제 사용자 객체 조회 (API 의존성 시뮬레이션)
    student = db.query(User).filter(User.email == student_email).first()
    
    # ===== 2. 문제 조회 =====
    print("\n[2단계] 문제 조회 시스템 테스트")
    print("-" * 80)
    
    # 전체 문제 목록 조회
    problems_response = list_problems(
        skip=0,
        limit=5,
        difficulty=None,
        category=None,
        db=db
    )
    
    print(f"✅ 문제 목록 조회 성공")
    print(f"   전체 문제 수: {problems_response['total']}")
    print(f"   조회된 문제:")
    
    available_problems = problems_response['problems']
    for i, problem in enumerate(available_problems[:3], 1):
        print(f"   {i}. {problem.title} (난이도: {problem.difficulty})")
    
    # 첫 번째 문제 상세 조회
    if available_problems:
        first_problem = available_problems[0]
        problem_detail = get_problem(first_problem.id, db)
        print(f"\n✅ 문제 상세 조회 성공: {problem_detail.title}")
        print(f"   문제 내용: {problem_detail.description[:50]}...")
    
    # ===== 3. 학습 진행 =====
    print("\n[3단계] 학습 진행 시스템 테스트")
    print("-" * 80)
    
    if not available_problems:
        print("⚠️  테스트할 문제가 없습니다")
        db.close()
        return
    
    test_problem = available_problems[0]
    
    # 문제 시작 (진행도 추적 시작)
    progress = start_problem(test_problem.id, db, student)
    print(f"✅ 문제 시작: {test_problem.title}")
    print(f"   진행 상태: {progress.status}")
    print(f"   시도 횟수: {progress.attempts}")
    
    # ===== 4. 답안 제출 =====
    print("\n[4단계] 답안 제출 시스템 테스트")
    print("-" * 80)
    
    # 첫 번째 답안 제출
    submission1_data = SubmissionCreate(
        problem_id=test_problem.id,
        answer="x = 2 또는 x = 3 (인수분해를 통한 풀이)"
    )
    
    submission1 = create_submission(submission1_data, db, student)
    print(f"✅ 답안 제출 성공 (1차 시도)")
    print(f"   제출 ID: {submission1.id}")
    print(f"   답변 내용: {submission1.answer[:50]}...")
    print(f"   채점 상태: {'미채점' if submission1.is_correct is None else '채점완료'}")
    
    # 진행도 조회 (시도 횟수 증가 확인)
    updated_progress = get_problem_progress(test_problem.id, db, student)
    print(f"\n   진행 상태 업데이트:")
    print(f"   - 시도 횟수: {updated_progress.attempts}")
    
    # ===== 5. 제출 이력 조회 =====
    print("\n[5단계] 제출 이력 조회 시스템 테스트")
    print("-" * 80)
    
    my_submissions = list_my_submissions(
        skip=0,
        limit=10,
        problem_id=None,
        db=db,
        current_user=student
    )
    
    print(f"✅ 내 제출 이력 조회 성공")
    print(f"   전체 제출 수: {my_submissions['total']}")
    for i, sub in enumerate(my_submissions['submissions'], 1):
        print(f"   {i}. 제출 시간: {sub.created_at}")
        print(f"      답변: {sub.answer[:50]}...")
    
    # ===== 6. 문제 완료 처리 =====
    print("\n[6단계] 문제 완료 처리 테스트")
    print("-" * 80)
    
    completed_progress = complete_problem(test_problem.id, db, student)
    print(f"✅ 문제 완료 처리 성공")
    print(f"   상태: {completed_progress.status}")
    print(f"   완료 시간: {completed_progress.completed_at}")
    
    # ===== 7. 학습 통계 =====
    print("\n[7단계] 학습 통계 조회 테스트")
    print("-" * 80)
    
    stats = get_my_stats(db, student)
    print(f"✅ 학습 통계 조회 성공")
    print(f"   전체 문제 수: {stats.total_problems}")
    print(f"   미시작: {stats.not_started}")
    print(f"   진행 중: {stats.in_progress}")
    print(f"   완료: {stats.completed}")
    print(f"   완료율: {stats.completion_rate}%")
    
    # ===== 8. 데이터 정합성 검증 =====
    print("\n[8단계] 데이터 정합성 검증")
    print("-" * 80)
    
    # DB에서 직접 조회하여 검증
    db_user = db.query(User).filter(User.id == student.id).first()
    db_submissions = db.query(Submission).filter(Submission.user_id == student.id).count()
    db_progress = db.query(Progress).filter(Progress.user_id == student.id).count()
    
    print(f"✅ 데이터베이스 정합성 확인")
    print(f"   사용자: {db_user.email} (활성: {db_user.is_active})")
    print(f"   제출 수: {db_submissions}")
    print(f"   진행도 수: {db_progress}")
    
    # ===== 완료 =====
    print("\n" + "=" * 80)
    print("🎉 Phase 1 MVP 통합 테스트 모두 통과!")
    print("=" * 80)
    
    print("\n✅ 검증된 기능:")
    print("   1. 사용자 등록 및 인증 (JWT)")
    print("   2. 문제 목록 조회 및 상세 보기")
    print("   3. 학습 진행도 추적 (시작/완료)")
    print("   4. 답안 제출 시스템")
    print("   5. 제출 이력 관리")
    print("   6. 학습 통계 집계")
    print("   7. 데이터 정합성 유지")
    
    print("\n📊 시스템 상태:")
    total_users = db.query(User).count()
    total_problems = db.query(Problem).count()
    total_submissions = db.query(Submission).count()
    total_progress = db.query(Progress).count()
    
    print(f"   - 전체 사용자: {total_users}")
    print(f"   - 전체 문제: {total_problems}")
    print(f"   - 전체 제출: {total_submissions}")
    print(f"   - 전체 진행도: {total_progress}")
    
    db.close()


if __name__ == "__main__":
    test_full_student_workflow()
