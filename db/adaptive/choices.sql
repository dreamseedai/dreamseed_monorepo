DROP TABLE IF EXISTS choices CASCADE;
CREATE TABLE choices (
  choice_id    SERIAL PRIMARY KEY,
  question_id  INT REFERENCES questions(question_id) ON DELETE CASCADE,
  content      TEXT NOT NULL,
  is_correct   BOOLEAN DEFAULT FALSE
);

