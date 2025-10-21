DROP TABLE IF EXISTS exams CASCADE;
CREATE TABLE exams (
  exam_id       SERIAL PRIMARY KEY,
  title         TEXT NOT NULL,
  subject       TEXT,
  description   TEXT,
  max_questions INT,
  time_limit    INT,
  created_by    INT REFERENCES users(user_id)
);

