-- Adaptive Exam Platform - Production Schema (no DROPs, no sample data)
-- Includes essential indexes for typical query patterns

-- Extension for UUID generation (safe if already installed)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
  org_id       SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  type         TEXT,
  region       TEXT
);

-- Topics (hierarchical)
CREATE TABLE IF NOT EXISTS topics (
  topic_id        SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  parent_topic_id INT REFERENCES topics(topic_id)
);
CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_topic_id);

-- Users
CREATE TABLE IF NOT EXISTS users (
  user_id         SERIAL PRIMARY KEY,
  email           VARCHAR(100) UNIQUE NOT NULL,
  password_hash   VARCHAR(200) NOT NULL,
  name            VARCHAR(100),
  role            VARCHAR(20) NOT NULL,
  organization_id INT REFERENCES organizations(org_id)
);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

-- Exams (catalog)
CREATE TABLE IF NOT EXISTS exams (
  exam_id       SERIAL PRIMARY KEY,
  title         TEXT NOT NULL,
  subject       TEXT,
  description   TEXT,
  max_questions INT,
  time_limit    INT,
  created_by    INT REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_exams_created_by ON exams(created_by);
CREATE INDEX IF NOT EXISTS idx_exams_subject ON exams(subject);

-- Exam Sessions (attempts)
CREATE TABLE IF NOT EXISTS exam_sessions (
  session_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exam_id          INT REFERENCES exams(exam_id),
  user_id          INT REFERENCES users(user_id),
  start_time       TIMESTAMP NOT NULL DEFAULT NOW(),
  end_time         TIMESTAMP,
  ability_estimate FLOAT,
  standard_error   FLOAT,
  final_score      INT,
  completed        BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_sessions_exam ON exam_sessions(exam_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON exam_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_completed ON exam_sessions(completed, end_time DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_user_exam ON exam_sessions(user_id, exam_id);

-- Questions (bank with IRT params)
CREATE TABLE IF NOT EXISTS questions (
  question_id          SERIAL PRIMARY KEY,
  content              TEXT NOT NULL,
  solution_explanation TEXT,
  topic_id             INT REFERENCES topics(topic_id),
  difficulty           FLOAT,
  discrimination       FLOAT,
  guessing             FLOAT,
  org_id               INT REFERENCES organizations(org_id),
  created_by           INT REFERENCES users(user_id),
  created_at           TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);
CREATE INDEX IF NOT EXISTS idx_questions_org ON questions(org_id);
CREATE INDEX IF NOT EXISTS idx_questions_creator ON questions(created_by);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);

-- Choices (MCQ options)
CREATE TABLE IF NOT EXISTS choices (
  choice_id    SERIAL PRIMARY KEY,
  question_id  INT REFERENCES questions(question_id) ON DELETE CASCADE,
  content      TEXT NOT NULL,
  is_correct   BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_choices_question ON choices(question_id);
CREATE INDEX IF NOT EXISTS idx_choices_correct ON choices(question_id, is_correct);

-- Responses (submitted answers)
CREATE TABLE IF NOT EXISTS responses (
  response_id     SERIAL PRIMARY KEY,
  session_id      UUID REFERENCES exam_sessions(session_id) ON DELETE CASCADE,
  question_id     INT REFERENCES questions(question_id),
  selected_choice INT REFERENCES choices(choice_id),
  is_correct      BOOLEAN,
  answered_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  ability_before  FLOAT,
  ability_after   FLOAT
);
CREATE INDEX IF NOT EXISTS idx_responses_session ON responses(session_id);
CREATE INDEX IF NOT EXISTS idx_responses_session_time ON responses(session_id, answered_at);
CREATE INDEX IF NOT EXISTS idx_responses_question ON responses(question_id);
CREATE INDEX IF NOT EXISTS idx_responses_choice ON responses(selected_choice);
CREATE INDEX IF NOT EXISTS idx_responses_question_time ON responses(question_id, answered_at);


