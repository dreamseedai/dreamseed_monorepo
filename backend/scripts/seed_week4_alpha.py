"""
Seed script for Week 4 alpha testing.

Creates:
- 3 Organizations (public school, academy, private tutor)
- 4 Teachers (1 school, 2 academy, 1 tutor) with OrgMemberships
- 3 Students with multi-organization enrollments
- Sample IRT abilities (θ values)
- Sample report comments (draft + published)

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/seed_week4_alpha.py
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.org_models import (
    Organization,
    OrgMembership,
    StudentOrgEnrollment,
    OrganizationType,
    OrgRole,
)
from app.models.report_models import (
    ReportComment,
    ReportSection,
    ReportSourceType,
)
from app.models.exam_models import IRTStudentAbility


# ============================================================================
# Test Data IDs (deterministic UUIDs for easy reference)
# ============================================================================

# Organizations
ORG_SCHOOL = uuid.UUID("11111111-1111-1111-1111-111111111111")
ORG_ACADEMY = uuid.UUID("22222222-2222-2222-2222-222222222222")
ORG_TUTOR = uuid.UUID("33333333-3333-3333-3333-333333333333")

# Teachers (TODO: Replace with real User UUIDs after user creation)
TEACHER_SCHOOL = uuid.UUID("44444444-4444-4444-4444-444444444444")
TEACHER_ACADEMY_1 = uuid.UUID("55555555-5555-5555-5555-555555555555")
TEACHER_ACADEMY_2 = uuid.UUID("66666666-6666-6666-6666-666666666666")
TEACHER_TUTOR = uuid.UUID("77777777-7777-7777-7777-777777777777")

# Students (TODO: Replace with real User UUIDs after user creation)
STUDENT_1 = uuid.UUID("88888888-8888-8888-8888-888888888888")  # 이민준 (Lee Min-jun)
STUDENT_2 = uuid.UUID("99999999-9999-9999-9999-999999999999")  # 김서연 (Kim Seo-yeon)
STUDENT_3 = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")  # 박지호 (Park Ji-ho)


# ============================================================================
# Seed Functions
# ============================================================================

async def seed_organizations(db: AsyncSession):
    """Create 3 test organizations."""
    orgs = [
        Organization(
            id=ORG_SCHOOL,
            name="서울고등학교",
            type=OrganizationType.PUBLIC_SCHOOL,
            external_code="SCHOOL-2025-001",
            is_active=True,
        ),
        Organization(
            id=ORG_ACADEMY,
            name="대치입시학원",
            type=OrganizationType.ACADEMY,
            external_code="ACADEMY-2025-042",
            is_active=True,
        ),
        Organization(
            id=ORG_TUTOR,
            name="김튜터 수학교실",
            type=OrganizationType.PRIVATE_TUTOR,
            external_code=None,
            is_active=True,
        ),
    ]
    
    db.add_all(orgs)
    await db.commit()
    print(f"✅ Created {len(orgs)} organizations")


async def seed_teacher_memberships(db: AsyncSession):
    """Create teacher memberships (4 teachers across 3 orgs)."""
    memberships = [
        # School teacher (head teacher)
        OrgMembership(
            user_id=TEACHER_SCHOOL,
            organization_id=ORG_SCHOOL,
            role=OrgRole.ORG_HEAD_TEACHER,
        ),
        # Academy teacher 1 (regular)
        OrgMembership(
            user_id=TEACHER_ACADEMY_1,
            organization_id=ORG_ACADEMY,
            role=OrgRole.ORG_TEACHER,
        ),
        # Academy teacher 2 (head teacher)
        OrgMembership(
            user_id=TEACHER_ACADEMY_2,
            organization_id=ORG_ACADEMY,
            role=OrgRole.ORG_HEAD_TEACHER,
        ),
        # Private tutor (admin of own org)
        OrgMembership(
            user_id=TEACHER_TUTOR,
            organization_id=ORG_TUTOR,
            role=OrgRole.ORG_ADMIN,
        ),
    ]
    
    db.add_all(memberships)
    await db.commit()
    print(f"✅ Created {len(memberships)} teacher memberships")


async def seed_student_enrollments(db: AsyncSession):
    """Create student enrollments (3 students, multi-org)."""
    enrollments = [
        # Student 1: 이민준 (all 3 organizations)
        StudentOrgEnrollment(
            student_id=STUDENT_1,
            organization_id=ORG_SCHOOL,
            label="2-3",  # Class 2-3
        ),
        StudentOrgEnrollment(
            student_id=STUDENT_1,
            organization_id=ORG_ACADEMY,
            label="SAT Prep A",
        ),
        StudentOrgEnrollment(
            student_id=STUDENT_1,
            organization_id=ORG_TUTOR,
            label=None,  # 1:1 tutoring
        ),
        
        # Student 2: 김서연 (school + academy)
        StudentOrgEnrollment(
            student_id=STUDENT_2,
            organization_id=ORG_SCHOOL,
            label="2-5",
        ),
        StudentOrgEnrollment(
            student_id=STUDENT_2,
            organization_id=ORG_ACADEMY,
            label="SAT Prep B",
        ),
        
        # Student 3: 박지호 (school + tutor)
        StudentOrgEnrollment(
            student_id=STUDENT_3,
            organization_id=ORG_SCHOOL,
            label="2-7",
        ),
        StudentOrgEnrollment(
            student_id=STUDENT_3,
            organization_id=ORG_TUTOR,
            label=None,
        ),
    ]
    
    db.add_all(enrollments)
    await db.commit()
    print(f"✅ Created {len(enrollments)} student enrollments")


async def seed_irt_abilities(db: AsyncSession):
    """Create sample IRT ability snapshots."""
    now = datetime.utcnow()
    abilities = [
        # Student 1 (이민준) - High performer
        IRTStudentAbility(
            user_id=STUDENT_1,
            subject="math",
            theta=0.85,
            theta_se=0.25,
            exam_id=None,
            calibrated_at=now - timedelta(days=7),
        ),
        IRTStudentAbility(
            user_id=STUDENT_1,
            subject="english",
            theta=0.42,
            theta_se=0.30,
            exam_id=None,
            calibrated_at=now - timedelta(days=5),
        ),
        IRTStudentAbility(
            user_id=STUDENT_1,
            subject="science",
            theta=-0.15,
            theta_se=0.35,
            exam_id=None,
            calibrated_at=now - timedelta(days=3),
        ),
        
        # Student 2 (김서연) - Average performer with recent decline
        IRTStudentAbility(
            user_id=STUDENT_2,
            subject="math",
            theta=-0.25,
            theta_se=0.40,
            exam_id=None,
            calibrated_at=now - timedelta(days=10),
        ),
        IRTStudentAbility(
            user_id=STUDENT_2,
            subject="english",
            theta=0.15,
            theta_se=0.28,
            exam_id=None,
            calibrated_at=now - timedelta(days=8),
        ),
        
        # Student 3 (박지호) - At-risk, high uncertainty
        IRTStudentAbility(
            user_id=STUDENT_3,
            subject="math",
            theta=-0.75,
            theta_se=0.65,  # High uncertainty
            exam_id=None,
            calibrated_at=now - timedelta(days=14),
        ),
        IRTStudentAbility(
            user_id=STUDENT_3,
            subject="science",
            theta=-0.50,
            theta_se=0.45,
            exam_id=None,
            calibrated_at=now - timedelta(days=12),
        ),
    ]
    
    db.add_all(abilities)
    await db.commit()
    print(f"✅ Created {len(abilities)} IRT ability snapshots")


async def seed_report_comments(db: AsyncSession):
    """Create sample report comments (school + academy + tutor)."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=30)
    period_end = now
    
    comments = [
        # School teacher comments for Student 1 (published)
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_SCHOOL,
            author_id=TEACHER_SCHOOL,
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.SUMMARY,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "최근 4주 동안 수학 실력이 꾸준히 향상되었습니다. "
                "특히 대수 문제 풀이에서 두각을 나타내고 있으며, "
                "학급 내 상위 10% 수준을 유지하고 있습니다. "
                "영어는 아직 안정화 단계이므로 추가 연습이 필요합니다."
            ),
            is_published=True,
        ),
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_SCHOOL,
            author_id=TEACHER_SCHOOL,
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.NEXT_4W_PLAN,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content="수학: 난이도 중상 문제 집중 연습 (주 3회, 각 1시간)",
            is_published=True,
        ),
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_SCHOOL,
            author_id=TEACHER_SCHOOL,
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.PARENT_GUIDANCE,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "자녀의 학습 패턴을 긍정적으로 유지하기 위해 정기적인 격려와 "
                "작은 목표 달성 시 칭찬을 아끼지 마세요. "
                "영어 독해 속도 향상을 위해 가정에서 주 2-3회 영문 기사 읽기를 권장합니다."
            ),
            is_published=True,
        ),
        
        # Academy teacher comments for Student 1 (published)
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_ACADEMY,
            author_id=TEACHER_ACADEMY_1,
            source_type=ReportSourceType.ACADEMY_TEACHER,
            section=ReportSection.SUMMARY,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "SAT 대비 과정에서 문제 풀이 속도가 크게 개선되었습니다. "
                "Math 섹션은 목표 점수 도달 가능 수준이며, "
                "Reading 섹션은 시간 관리 훈련이 더 필요합니다."
            ),
            is_published=True,
        ),
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_ACADEMY,
            author_id=TEACHER_ACADEMY_1,
            source_type=ReportSourceType.ACADEMY_TEACHER,
            section=ReportSection.NEXT_4W_PLAN,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content="주 3회 모의고사 응시 (실전 시간 제한 준수)",
            is_published=True,
        ),
        
        # Private tutor comments for Student 1 (published)
        ReportComment(
            student_id=STUDENT_1,
            organization_id=ORG_TUTOR,
            author_id=TEACHER_TUTOR,
            source_type=ReportSourceType.TUTOR,
            section=ReportSection.SUMMARY,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "1:1 수학 과외에서 기초 개념 정리가 잘 되었습니다. "
                "특히 함수와 그래프 단원에서 실력 향상이 두드러졌습니다. "
                "다음 단계로 응용 문제 풀이 전략을 집중적으로 다룰 예정입니다."
            ),
            is_published=True,
        ),
        
        # School teacher comments for Student 3 (at-risk, published)
        ReportComment(
            student_id=STUDENT_3,
            organization_id=ORG_SCHOOL,
            author_id=TEACHER_SCHOOL,
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.SUMMARY,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "최근 4주 동안 수학 성적이 하락 추세를 보이고 있습니다. "
                "기초 개념 이해에 어려움이 있는 것으로 판단되며, "
                "추가 보충 학습이 시급합니다. "
                "과학도 유사한 패턴을 보이고 있어 종합적인 학습 전략 재정비가 필요합니다."
            ),
            is_published=True,
        ),
        ReportComment(
            student_id=STUDENT_3,
            organization_id=ORG_SCHOOL,
            author_id=TEACHER_SCHOOL,
            source_type=ReportSourceType.SCHOOL_TEACHER,
            section=ReportSection.PARENT_GUIDANCE,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content=(
                "가정에서 학습 시간을 점검하고, 규칙적인 복습 패턴을 확립해 주세요. "
                "튜터와의 긴밀한 협력을 통해 기초부터 차근차근 다시 쌓아올리는 것이 중요합니다. "
                "현재 상태로는 다음 학기 진도를 따라가기 어려울 수 있습니다."
            ),
            is_published=True,
        ),
        
        # Draft comment (not published)
        ReportComment(
            student_id=STUDENT_2,
            organization_id=ORG_ACADEMY,
            author_id=TEACHER_ACADEMY_2,
            source_type=ReportSourceType.ACADEMY_TEACHER,
            section=ReportSection.SUMMARY,
            language="ko",
            period_start=period_start,
            period_end=period_end,
            content="[초안] 최근 학습 동기가 다소 저하된 것으로 보입니다...",
            is_published=False,  # Draft only
        ),
    ]
    
    db.add_all(comments)
    await db.commit()
    print(f"✅ Created {len(comments)} report comments")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run all seed functions."""
    print("=" * 60)
    print("Week 4 Alpha Test - Seed Script")
    print("=" * 60)
    
    async with async_session_maker() as db:
        try:
            print("\n1️⃣  Seeding organizations...")
            await seed_organizations(db)
            
            print("\n2️⃣  Seeding teacher memberships...")
            await seed_teacher_memberships(db)
            
            print("\n3️⃣  Seeding student enrollments...")
            await seed_student_enrollments(db)
            
            print("\n4️⃣  Seeding IRT ability snapshots...")
            await seed_irt_abilities(db)
            
            print("\n5️⃣  Seeding report comments...")
            await seed_report_comments(db)
            
            print("\n" + "=" * 60)
            print("✅ All seed data created successfully!")
            print("=" * 60)
            
            print("\n📋 Summary:")
            print("   - 3 Organizations (school, academy, tutor)")
            print("   - 4 Teachers with memberships")
            print("   - 3 Students with multi-org enrollments")
            print("   - 7 IRT ability snapshots")
            print("   - 9 Report comments (8 published, 1 draft)")
            
            print("\n🔑 Test User IDs (update these with real User UUIDs):")
            print(f"   School Teacher:  {TEACHER_SCHOOL}")
            print(f"   Academy Teacher: {TEACHER_ACADEMY_1}, {TEACHER_ACADEMY_2}")
            print(f"   Private Tutor:   {TEACHER_TUTOR}")
            print(f"   Students:        {STUDENT_1}, {STUDENT_2}, {STUDENT_3}")
            
            print("\n🧪 Next Steps:")
            print("   1. Create actual User accounts (via FastAPI-Users)")
            print("   2. Update UUIDs in this script with real user IDs")
            print("   3. Re-run script: python scripts/seed_week4_alpha.py")
            print("   4. Test APIs: curl commands in ORGANIZATION_AND_MULTI_SOURCE_REPORTS.md")
            print("   5. Test UIs: student_front, tutor_front, parent_front")
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
