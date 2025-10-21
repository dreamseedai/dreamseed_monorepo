DROP TABLE IF EXISTS responses CASCADE;
CREATE TABLE responses (
  response_id    SERIAL PRIMARY KEY,
  session_id     UUID REFERENCES exam_sessions(session_id) ON DELETE CASCADE,
  question_id    INT REFERENCES questions(question_id),
  selected_choice INT REFERENCES choices(choice_id),
  is_correct     BOOLEAN,
  answered_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  ability_before FLOAT,
  ability_after  FLOAT
);

