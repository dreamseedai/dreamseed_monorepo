CREATE TABLE IF NOT EXISTS `dreamseedai-prod.seedtest.fact_responses` (
  event_id STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  org_id INT64 NOT NULL,
  session_id STRING NOT NULL,
  user_id INT64 NOT NULL,
  question_id INT64 NOT NULL,
  is_correct BOOL NOT NULL,
  elapsed_ms INT64 NOT NULL,
  ability_before FLOAT64,
  ability_after FLOAT64,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(occurred_at)
CLUSTER BY org_id, question_id;

