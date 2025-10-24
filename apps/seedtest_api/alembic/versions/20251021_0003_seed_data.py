from alembic import op, context
import os

# revision identifiers, used by Alembic.
revision = '20251021_0003_seed_data'
down_revision = '20251021_0002_indexes_and_fks'
branch_labels = None
depends_on = None


def upgrade():
    # Optional seed: run only when invoked with `-x seed=true` (or any truthy)
    x = context.get_x_argument(as_dictionary=True)
    seed_flag = str(x.get('seed', os.getenv('ALEMBIC_SEED', ''))).lower() in ('1', 'true', 'yes', 'on')
    if not seed_flag:
        return
    # Organizations
    op.execute("""
    INSERT INTO organizations (name, type, region)
    VALUES ('Global Platform', 'Platform', 'N/A')
    ON CONFLICT DO NOTHING;
    """)

    # Topics hierarchy
    op.execute("""
    INSERT INTO topics (topic_id, name, parent_topic_id) VALUES
    (1, 'Mathematics', NULL)
    ON CONFLICT DO NOTHING;
    """)
    op.execute("""
    INSERT INTO topics (name, parent_topic_id) VALUES
    ('Probability and Statistics', 1),
    ('Algebra', 1);
    """)

    # Users (teacher + student)
    op.execute("""
    INSERT INTO users (email, password_hash, name, role, organization_id) VALUES
    ('teacher1@example.com', 'hashed_pw_123', 'Teacher One', 'teacher', 1),
    ('student1@example.com', 'hashed_pw_456', 'Student One', 'student', 1)
    ON CONFLICT (email) DO NOTHING;
    """)

    # Exam catalog
    op.execute("""
    INSERT INTO exams (title, subject, description, max_questions, time_limit, created_by) VALUES
    ('Math Adaptive Test 2025', 'Mathematics', 'Adaptive math test example', 20, 60, (SELECT user_id FROM users WHERE email='teacher1@example.com' LIMIT 1));
    """)

    # Questions with dummy IRT params
    op.execute("""
    INSERT INTO questions (content, solution_explanation, topic_id, difficulty, discrimination, guessing, org_id, created_by)
    VALUES 
    (
      'If a fair coin is flipped twice, what is the probability of getting two heads?',
      'There are 4 possible outcomes...',
      (SELECT topic_id FROM topics WHERE name='Probability and Statistics' LIMIT 1),
      0.5, 1.0, 0.25, NULL,
      (SELECT user_id FROM users WHERE email='teacher1@example.com' LIMIT 1)
    ),
    (
      'Solve for x: 2x + 3 = 7',
      'Isolate x: 2x = 4, so x = 2.',
      (SELECT topic_id FROM topics WHERE name='Algebra' LIMIT 1),
      -0.5, 0.8, 0.25, NULL,
      (SELECT user_id FROM users WHERE email='teacher1@example.com' LIMIT 1)
    );
    """)

    # Choices for questions (assumes sequential IDs)
    op.execute("""
    WITH q1 AS (
      SELECT question_id AS id FROM questions WHERE content LIKE 'If a fair coin%' ORDER BY question_id DESC LIMIT 1
    )
    INSERT INTO choices (question_id, content, is_correct) VALUES
    ((SELECT id FROM q1), '0.25', TRUE),
    ((SELECT id FROM q1), '0.5', FALSE),
    ((SELECT id FROM q1), '0.75', FALSE),
    ((SELECT id FROM q1), '0', FALSE);
    """)
    op.execute("""
    WITH q2 AS (
      SELECT question_id AS id FROM questions WHERE content LIKE 'Solve for x:%' ORDER BY question_id DESC LIMIT 1
    )
    INSERT INTO choices (question_id, content, is_correct) VALUES
    ((SELECT id FROM q2), '2', TRUE),
    ((SELECT id FROM q2), '4', FALSE),
    ((SELECT id FROM q2), '1', FALSE),
    ((SELECT id FROM q2), '0', FALSE);
    """)


def downgrade():
    # Optional cleanup: only when -x seed=true supplied; otherwise keep data intact
    x = context.get_x_argument(as_dictionary=True)
    seed_flag = str(x.get('seed', os.getenv('ALEMBIC_SEED', ''))).lower() in ('1', 'true', 'yes', 'on')
    if not seed_flag:
        return
    # Best-effort cleanup of seeded rows
    op.execute("""
    DELETE FROM choices WHERE question_id IN (
      SELECT question_id FROM questions WHERE content LIKE 'If a fair coin%' OR content LIKE 'Solve for x:%'
    );
    """)
    op.execute("""
    DELETE FROM questions WHERE content LIKE 'If a fair coin%' OR content LIKE 'Solve for x:%';
    """)
    op.execute("DELETE FROM exams WHERE title='Math Adaptive Test 2025';")
    op.execute("""
    DELETE FROM users WHERE email IN ('teacher1@example.com','student1@example.com');
    """)
    op.execute("""
    DELETE FROM topics WHERE name IN ('Probability and Statistics','Algebra');
    """)
    op.execute("DELETE FROM topics WHERE name='Mathematics';")
    op.execute("DELETE FROM organizations WHERE name='Global Platform';")


