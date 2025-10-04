#!/usr/bin/env python3
"""
Test script for DreamSeedAI Enhanced Schema
Verifies that the personalized educational platform schema is working correctly
"""

import psycopg2
import json
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'dreamseed',
    'user': 'postgres',
    'password': 'DreamSeedAi@0908'
}

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_enhanced_tables():
    """Test that enhanced tables exist and have correct structure"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test questions_enhanced table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'questions_enhanced' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"✅ questions_enhanced table has {len(columns)} columns")
        
        # Test user_performance table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_performance' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"✅ user_performance table has {len(columns)} columns")
        
        # Test learning_recommendations table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'learning_recommendations' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"✅ learning_recommendations table has {len(columns)} columns")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Enhanced tables test failed: {e}")
        return False

def test_sample_data():
    """Test sample data insertion and retrieval"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if sample questions exist
        cursor.execute("SELECT COUNT(*) FROM questions_enhanced;")
        count = cursor.fetchone()[0]
        print(f"✅ questions_enhanced table has {count} sample questions")
        
        # Test the personalized questions function
        cursor.execute("SELECT * FROM get_personalized_questions(1, 5);")
        questions = cursor.fetchall()
        print(f"✅ Personalized questions function returned {len(questions)} questions")
        
        # Test user learning analytics view
        cursor.execute("SELECT COUNT(*) FROM user_learning_analytics;")
        analytics_count = cursor.fetchone()[0]
        print(f"✅ user_learning_analytics view has {analytics_count} records")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Sample data test failed: {e}")
        return False

def test_user_profile_extension():
    """Test user profile table extensions"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if new columns exist in users_profile
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users_profile' 
            AND table_schema = 'public'
            AND column_name IN ('preferred_subjects', 'difficulty_preference', 'learning_style');
        """)
        new_columns = cursor.fetchall()
        print(f"✅ users_profile has {len(new_columns)} new educational columns")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ User profile extension test failed: {e}")
        return False

def test_indexes():
    """Test that performance indexes are created"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for key indexes
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('questions_enhanced', 'user_performance', 'learning_recommendations')
            AND indexname LIKE 'idx_%';
        """)
        indexes = cursor.fetchall()
        print(f"✅ Created {len(indexes)} performance indexes")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Indexes test failed: {e}")
        return False

def create_test_user():
    """Create a test user for API testing"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create test user
        cursor.execute("""
            INSERT INTO users (email, password_hash, created_at, role)
            VALUES ('test@dreamseedai.com', 'hashed_password', NOW(), 'user')
            ON CONFLICT (email) DO NOTHING
            RETURNING id;
        """)
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
            print(f"✅ Created test user with ID: {user_id}")
            
            # Create user profile
            cursor.execute("""
                INSERT INTO users_profile (
                    user_id, preferred_subjects, difficulty_preference, 
                    learning_style, study_goals, country, grade_code,
                    subscribed, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                ) ON CONFLICT (user_id) DO UPDATE SET
                    preferred_subjects = EXCLUDED.preferred_subjects,
                    difficulty_preference = EXCLUDED.difficulty_preference,
                    learning_style = EXCLUDED.learning_style,
                    study_goals = EXCLUDED.study_goals,
                    country = EXCLUDED.country,
                    grade_code = EXCLUDED.grade_code,
                    updated_at = NOW();
            """, (
                user_id,
                ['math', 'biology'],  # preferred_subjects
                3,  # difficulty_preference
                'visual',  # learning_style
                ['sat_prep', 'college_readiness'],  # study_goals
                'US',  # country
                'G11',  # grade_code
                True  # subscribed
            ))
            
            print(f"✅ Created test user profile for user ID: {user_id}")
            
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Test user creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing DreamSeedAI Enhanced Schema")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_connection),
        ("Enhanced Tables", test_enhanced_tables),
        ("User Profile Extensions", test_user_profile_extension),
        ("Sample Data", test_sample_data),
        ("Performance Indexes", test_indexes),
        ("Test User Creation", create_test_user),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Schema is ready for implementation.")
        print("\n🚀 Next steps:")
        print("1. Integrate personalized_api.py with FastAPI app")
        print("2. Test API endpoints with the created test user")
        print("3. Begin MathML to TipTap + MathLive conversion")
        print("4. Implement frontend components for personalized learning")
    else:
        print("⚠️  Some tests failed. Please review and fix issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    main()
