from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251021_0002_indexes_and_fks'
down_revision = '20251021_0001_init'
branch_labels = None
depends_on = None


def upgrade():
    # Add foreign keys
    op.create_foreign_key(None, 'topics', 'topics', ['parent_topic_id'], ['topic_id'])
    op.create_foreign_key(None, 'users', 'organizations', ['organization_id'], ['org_id'])
    op.create_foreign_key(None, 'exams', 'users', ['created_by'], ['user_id'])
    op.create_foreign_key(None, 'questions', 'topics', ['topic_id'], ['topic_id'])
    op.create_foreign_key(None, 'questions', 'organizations', ['org_id'], ['org_id'])
    op.create_foreign_key(None, 'questions', 'users', ['created_by'], ['user_id'])
    op.create_foreign_key(None, 'choices', 'questions', ['question_id'], ['question_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'exam_sessions', 'exams', ['exam_id'], ['exam_id'])
    op.create_foreign_key(None, 'exam_sessions', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key(None, 'responses', 'exam_sessions', ['session_id'], ['session_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'responses', 'questions', ['question_id'], ['question_id'])
    op.create_foreign_key(None, 'responses', 'choices', ['selected_choice'], ['choice_id'])

    # Indexes
    op.create_index('idx_topics_parent', 'topics', ['parent_topic_id'], if_not_exists=True)
    op.create_index('idx_users_org', 'users', ['organization_id'], if_not_exists=True)
    op.create_index('idx_exams_created_by', 'exams', ['created_by'], if_not_exists=True)
    op.create_index('idx_exams_subject', 'exams', ['subject'], if_not_exists=True)
    op.create_index('idx_questions_topic', 'questions', ['topic_id'], if_not_exists=True)
    op.create_index('idx_questions_org', 'questions', ['org_id'], if_not_exists=True)
    op.create_index('idx_questions_creator', 'questions', ['created_by'], if_not_exists=True)
    op.create_index('idx_questions_difficulty', 'questions', ['difficulty'], if_not_exists=True)
    op.create_index('idx_choices_question', 'choices', ['question_id'], if_not_exists=True)
    op.create_index('idx_choices_correct', 'choices', ['question_id', 'is_correct'], if_not_exists=True)
    op.create_index('idx_sessions_exam', 'exam_sessions', ['exam_id'], if_not_exists=True)
    op.create_index('idx_sessions_user', 'exam_sessions', ['user_id'], if_not_exists=True)
    op.create_index('idx_sessions_completed', 'exam_sessions', ['completed', 'end_time'], if_not_exists=True)
    op.create_index('idx_sessions_user_exam', 'exam_sessions', ['user_id', 'exam_id'], if_not_exists=True)
    op.create_index('idx_responses_session', 'responses', ['session_id'], if_not_exists=True)
    op.create_index('idx_responses_session_time', 'responses', ['session_id', 'answered_at'], if_not_exists=True)
    op.create_index('idx_responses_question', 'responses', ['question_id'], if_not_exists=True)
    op.create_index('idx_responses_choice', 'responses', ['selected_choice'], if_not_exists=True)
    op.create_index('idx_responses_question_time', 'responses', ['question_id', 'answered_at'], if_not_exists=True)


def downgrade():
    # Drop indexes (FKs will be dropped with tables in base downgrade)
    op.drop_index('idx_responses_question_time', table_name='responses', if_exists=True)
    op.drop_index('idx_responses_choice', table_name='responses', if_exists=True)
    op.drop_index('idx_responses_question', table_name='responses', if_exists=True)
    op.drop_index('idx_responses_session_time', table_name='responses', if_exists=True)
    op.drop_index('idx_responses_session', table_name='responses', if_exists=True)
    op.drop_index('idx_sessions_user_exam', table_name='exam_sessions', if_exists=True)
    op.drop_index('idx_sessions_completed', table_name='exam_sessions', if_exists=True)
    op.drop_index('idx_sessions_user', table_name='exam_sessions', if_exists=True)
    op.drop_index('idx_sessions_exam', table_name='exam_sessions', if_exists=True)
    op.drop_index('idx_choices_correct', table_name='choices', if_exists=True)
    op.drop_index('idx_choices_question', table_name='choices', if_exists=True)
    op.drop_index('idx_questions_difficulty', table_name='questions', if_exists=True)
    op.drop_index('idx_questions_creator', table_name='questions', if_exists=True)
    op.drop_index('idx_questions_org', table_name='questions', if_exists=True)
    op.drop_index('idx_questions_topic', table_name='questions', if_exists=True)
    op.drop_index('idx_exams_subject', table_name='exams', if_exists=True)
    op.drop_index('idx_exams_created_by', table_name='exams', if_exists=True)
    op.drop_index('idx_users_org', table_name='users', if_exists=True)
    op.drop_index('idx_topics_parent', table_name='topics', if_exists=True)


