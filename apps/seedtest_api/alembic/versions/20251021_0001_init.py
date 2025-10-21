from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251021_0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        'organizations',
        sa.Column('org_id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('type', sa.Text),
        sa.Column('region', sa.Text),
    )

    op.create_table(
        'topics',
        sa.Column('topic_id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('parent_topic_id', sa.Integer, sa.ForeignKey('topics.topic_id')),
    )
    op.create_index('idx_topics_parent', 'topics', ['parent_topic_id'])

    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(200), nullable=False),
        sa.Column('name', sa.String(100)),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('organization_id', sa.Integer, sa.ForeignKey('organizations.org_id')),
    )
    op.create_index('idx_users_org', 'users', ['organization_id'])

    op.create_table(
        'exams',
        sa.Column('exam_id', sa.Integer, primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('subject', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('max_questions', sa.Integer),
        sa.Column('time_limit', sa.Integer),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id')),
    )
    op.create_index('idx_exams_created_by', 'exams', ['created_by'])

    op.create_table(
        'questions',
        sa.Column('question_id', sa.Integer, primary_key=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('solution_explanation', sa.Text),
        sa.Column('topic_id', sa.Integer, sa.ForeignKey('topics.topic_id')),
        sa.Column('difficulty', sa.Float),
        sa.Column('discrimination', sa.Float),
        sa.Column('guessing', sa.Float),
        sa.Column('org_id', sa.Integer, sa.ForeignKey('organizations.org_id')),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.user_id')),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_questions_topic', 'questions', ['topic_id'])
    op.create_index('idx_questions_org', 'questions', ['org_id'])
    op.create_index('idx_questions_creator', 'questions', ['created_by'])
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'])

    op.create_table(
        'choices',
        sa.Column('choice_id', sa.Integer, primary_key=True),
        sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.question_id', ondelete='CASCADE')),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean, server_default=sa.text('false')),
    )
    op.create_index('idx_choices_question', 'choices', ['question_id'])
    op.create_index('idx_choices_correct', 'choices', ['question_id', 'is_correct'])

    op.create_table(
        'exam_sessions',
        sa.Column('session_id', sa.dialects.postgresql.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('exam_id', sa.Integer, sa.ForeignKey('exams.exam_id')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.user_id')),
        sa.Column('start_time', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP),
        sa.Column('ability_estimate', sa.Float),
        sa.Column('standard_error', sa.Float),
        sa.Column('final_score', sa.Integer),
        sa.Column('completed', sa.Boolean, server_default=sa.text('false')),
    )
    op.create_index('idx_sessions_exam', 'exam_sessions', ['exam_id'])
    op.create_index('idx_sessions_user', 'exam_sessions', ['user_id'])
    op.create_index('idx_sessions_completed', 'exam_sessions', ['completed', 'end_time'])

    op.create_table(
        'responses',
        sa.Column('response_id', sa.Integer, primary_key=True),
        sa.Column('session_id', sa.dialects.postgresql.UUID, sa.ForeignKey('exam_sessions.session_id', ondelete='CASCADE')),
        sa.Column('question_id', sa.Integer, sa.ForeignKey('questions.question_id')),
        sa.Column('selected_choice', sa.Integer, sa.ForeignKey('choices.choice_id')),
        sa.Column('is_correct', sa.Boolean),
        sa.Column('answered_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('ability_before', sa.Float),
        sa.Column('ability_after', sa.Float),
    )
    op.create_index('idx_responses_session', 'responses', ['session_id'])
    op.create_index('idx_responses_session_time', 'responses', ['session_id', 'answered_at'])
    op.create_index('idx_responses_question', 'responses', ['question_id'])
    op.create_index('idx_responses_choice', 'responses', ['selected_choice'])


def downgrade():
    op.drop_table('responses')
    op.drop_table('exam_sessions')
    op.drop_table('choices')
    op.drop_table('questions')
    op.drop_table('exams')
    op.drop_table('users')
    op.drop_table('topics')
    op.drop_table('organizations')


