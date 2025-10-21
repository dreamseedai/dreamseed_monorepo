DROP TABLE IF EXISTS questions CASCADE;
CREATE TABLE questions (
  question_id         SERIAL PRIMARY KEY,
  content             TEXT NOT NULL,
  solution_explanation TEXT,
  topic_id            INT REFERENCES topics(topic_id),
  difficulty          FLOAT,
  discrimination      FLOAT,
  guessing            FLOAT,
  org_id              INT REFERENCES organizations(org_id),
  created_by          INT REFERENCES users(user_id),
  created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

