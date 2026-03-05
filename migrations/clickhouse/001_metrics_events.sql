-- ClickHouse metrics events table scaffold
-- timestamp: 2026-03-04_20-12-00

CREATE TABLE IF NOT EXISTS metrics_events (
  event_type String,
  payload_json String,
  created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (event_type, created_at);
