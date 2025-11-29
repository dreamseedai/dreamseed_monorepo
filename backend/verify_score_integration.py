"""
Verify that score_utils integration is working correctly
by checking ExamSession records in the database.
"""
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.models import ExamSession
from app.core.services.score_utils import summarize_theta

# Database connection
DATABASE_URL = "postgresql://dreamseed_user:dreamseed_pass@localhost:5432/dreamseed_db_test"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def verify_score_integration():
    """Check if completed exam sessions have proper score/grade data."""
    db = SessionLocal()
    try:
        # Find completed exam sessions
        stmt = select(ExamSession).where(ExamSession.status == "completed")
        completed_sessions = db.execute(stmt).scalars().all()
        
        if not completed_sessions:
            print("❌ No completed exam sessions found in database")
            return False
        
        print(f"✅ Found {len(completed_sessions)} completed exam session(s)\n")
        
        all_valid = True
        for session in completed_sessions:
            print(f"📋 ExamSession {session.id}:")
            print(f"   Status: {session.status}")
            print(f"   Theta: {session.theta}")
            print(f"   Score: {session.score}")
            print(f"   Meta: {session.meta}")
            
            # Verify score field is populated
            if session.score is None:
                print(f"   ❌ Score is None (should be populated)")
                all_valid = False
            else:
                print(f"   ✅ Score populated: {session.score}")
            
            # Verify meta contains grade information
            if not session.meta:
                print(f"   ❌ Meta is None or empty (should contain grades)")
                all_valid = False
            else:
                required_keys = ["t_score", "percentile", "grade_numeric", "grade_letter"]
                missing_keys = [k for k in required_keys if k not in session.meta]
                
                if missing_keys:
                    print(f"   ❌ Meta missing keys: {missing_keys}")
                    all_valid = False
                else:
                    print(f"   ✅ Meta contains all grade info:")
                    print(f"      - T-Score: {session.meta.get('t_score')}")
                    print(f"      - Percentile: {session.meta.get('percentile')}")
                    print(f"      - Grade (Numeric): {session.meta.get('grade_numeric')}")
                    print(f"      - Grade (Letter): {session.meta.get('grade_letter')}")
            
            # Verify score matches expected value from theta
            if session.theta is not None:
                expected = summarize_theta(float(session.theta))
                if session.score is not None:
                    score_diff = abs(float(session.score) - expected["score_0_100"])
                    if score_diff > 0.01:
                        print(f"   ⚠️  Score mismatch: stored={session.score}, expected={expected['score_0_100']}")
                        all_valid = False
                    else:
                        print(f"   ✅ Score matches expected value")
            
            print()
        
        if all_valid:
            print("✅ All completed sessions have proper score/grade data")
        else:
            print("❌ Some sessions are missing score/grade data")
        
        return all_valid
        
    finally:
        db.close()

if __name__ == "__main__":
    success = verify_score_integration()
    sys.exit(0 if success else 1)
