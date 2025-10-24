CREATE EXTENSION IF NOT EXISTS pgcrypto;
DROP TABLE IF EXISTS exam_sessions CASCADE;
CREATE TABLE exam_sessions (
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

