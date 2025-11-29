-- DreamSeedAI Analytics - Materialized Views for Drift Monitoring
-- schemas: analytics (create if not exists)

CREATE SCHEMA IF NOT EXISTS analytics;

-- behavior_metrics: last_option_rate, omit_rate (by day/lang/region)
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.behavior_metrics AS
SELECT
  date_trunc('day', r.ts) AS ts,
  COALESCE(u.language, 'unknown') AS user_lang,
  COALESCE(u.region, 'unknown') AS region,
  AVG(CASE WHEN r.choice_idx = r.max_idx THEN 1.0 ELSE 0.0 END) AS last_option_rate,
  AVG(CASE WHEN r.choice_idx IS NULL THEN 1.0 ELSE 0.0 END) AS omit_rate
FROM responses r
LEFT JOIN users u ON u.id = r.user_id
GROUP BY 1,2,3;

CREATE INDEX IF NOT EXISTS idx_behavior_metrics_ts ON analytics.behavior_metrics(ts);
CREATE INDEX IF NOT EXISTS idx_behavior_metrics_lang ON analytics.behavior_metrics(user_lang);
CREATE INDEX IF NOT EXISTS idx_behavior_metrics_region ON analytics.behavior_metrics(region);

-- latency_metrics: median latency per day/lang/region
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.latency_metrics AS
SELECT
  date_trunc('day', r.ts) AS ts,
  COALESCE(u.language, 'unknown') AS user_lang,
  COALESCE(u.region, 'unknown') AS region,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (r.submit_ts - r.open_ts))) AS latency_s
FROM responses r
LEFT JOIN users u ON u.id = r.user_id
WHERE r.open_ts IS NOT NULL AND r.submit_ts IS NOT NULL
GROUP BY 1,2,3;

CREATE INDEX IF NOT EXISTS idx_latency_metrics_ts ON analytics.latency_metrics(ts);

-- daily_metrics: Δθ(7d) etc. (assumes per-user ability table `ability_daily(user_id, ts, theta)`)
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.daily_metrics AS
WITH d AS (
  SELECT ad.user_id, ad.ts::date AS ts, ad.theta,
         LAG(ad.theta,7) OVER (PARTITION BY ad.user_id ORDER BY ad.ts) AS theta_7d_ago
  FROM ability_daily ad
)
SELECT
  ts,
  COALESCE(u.language,'unknown') AS user_lang,
  COALESCE(u.region,'unknown') AS region,
  AVG(theta - theta_7d_ago) AS delta_theta_7d
FROM d
LEFT JOIN users u ON u.id = d.user_id
WHERE theta_7d_ago IS NOT NULL
GROUP BY 1,2,3;

CREATE INDEX IF NOT EXISTS idx_daily_metrics_ts ON analytics.daily_metrics(ts);

-- irt_anchor_deltas: per-anchor parameter deltas (requires item_params_daily with a,b,c)
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.irt_anchor_deltas AS
SELECT
  i.item_id,
  i.ts,
  i.a - LAG(i.a, 1) OVER (PARTITION BY i.item_id ORDER BY i.ts) AS delta_a_7d,
  i.b - LAG(i.b, 1) OVER (PARTITION BY i.item_id ORDER BY i.ts) AS delta_b_7d,
  i.c - LAG(i.c, 1) OVER (PARTITION BY i.item_id ORDER BY i.ts) AS delta_c_7d
FROM item_params_weekly i
WHERE i.is_anchor = true;

CREATE INDEX IF NOT EXISTS idx_irt_anchor_deltas_ts ON analytics.irt_anchor_deltas(ts);
CREATE INDEX IF NOT EXISTS idx_irt_anchor_deltas_item ON analytics.irt_anchor_deltas(item_id);

-- alerts table (if not exists)
CREATE TABLE IF NOT EXISTS analytics.alerts (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  alert_type TEXT NOT NULL,
  user_lang TEXT,
  region TEXT,
  payload JSONB,
  resolved BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_alerts_ts ON analytics.alerts(ts);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON analytics.alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON analytics.alerts(resolved);

-- Refresh commands (run via cron/celery)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.behavior_metrics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.latency_metrics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.daily_metrics;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.irt_anchor_deltas;
