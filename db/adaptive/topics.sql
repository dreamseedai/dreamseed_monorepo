DROP TABLE IF EXISTS topics CASCADE;
CREATE TABLE topics (
  topic_id        SERIAL PRIMARY KEY,
  name            TEXT NOT NULL,
  parent_topic_id INT REFERENCES topics(topic_id)
);

