from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251021_0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Base tables only (no indexes, no foreign keys)
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
        sa.Column('parent_topic_id', sa.Integer),
    )

    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(200), nullable=False),
        sa.Column('name', sa.String(100)),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('organization_id', sa.Integer),
    )

    op.create_table(
        'exams',
        sa.Column('exam_id', sa.Integer, primary_key=True),
        sa.Column('title', sa.Text, nullable=False),
        sa.Column('subject', sa.Text),
        sa.Column('description', sa.Text),
        sa.Column('max_questions', sa.Integer),
        sa.Column('time_limit', sa.Integer),
        sa.Column('created_by', sa.Integer),
    )

    op.create_table(
        'questions',
        sa.Column('question_id', sa.Integer, primary_key=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('solution_explanation', sa.Text),
        sa.Column('topic_id', sa.Integer),
        sa.Column('difficulty', sa.Float),
        sa.Column('discrimination', sa.Float),
        sa.Column('guessing', sa.Float),
        sa.Column('org_id', sa.Integer),
        sa.Column('created_by', sa.Integer),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'choices',
        sa.Column('choice_id', sa.Integer, primary_key=True),
        sa.Column('question_id', sa.Integer),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_correct', sa.Boolean, server_default=sa.text('false')),
    )

    op.create_table(
        'exam_sessions',
        sa.Column('session_id', sa.dialects.postgresql.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('exam_id', sa.Integer),
        sa.Column('user_id', sa.Integer),
        sa.Column('start_time', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP),
        sa.Column('ability_estimate', sa.Float),
        sa.Column('standard_error', sa.Float),
        sa.Column('final_score', sa.Integer),
        sa.Column('completed', sa.Boolean, server_default=sa.text('false')),
    )

    op.create_table(
        'responses',
        sa.Column('response_id', sa.Integer, primary_key=True),
        sa.Column('session_id', sa.dialects.postgresql.UUID),
        sa.Column('question_id', sa.Integer),
        sa.Column('selected_choice', sa.Integer),
        sa.Column('is_correct', sa.Boolean),
        sa.Column('answered_at', sa.TIMESTAMP, server_default=sa.text('NOW()'), nullable=False),
        sa.Column('ability_before', sa.Float),
        sa.Column('ability_after', sa.Float),
    )


def downgrade():
    op.drop_table('responses')
    op.drop_table('exam_sessions')
    op.drop_table('choices')
    op.drop_table('questions')
    op.drop_table('exams')
    op.drop_table('users')
    op.drop_table('topics')
    op.drop_table('organizations')


