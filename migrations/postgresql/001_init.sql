-- Phase 2 migration scaffold for PostgreSQL
-- timestamp: 2026-03-04_19-46-56

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  goal TEXT NOT NULL,
  created_at DOUBLE PRECISION NOT NULL,
  core_pause_level INTEGER NOT NULL,
  status TEXT NOT NULL,
  progress DOUBLE PRECISION NOT NULL,
  eta_seconds DOUBLE PRECISION,
  eta_confidence DOUBLE PRECISION NOT NULL,
  planned_seconds INTEGER NOT NULL,
  started_at DOUBLE PRECISION,
  completed_at DOUBLE PRECISION,
  error TEXT
);

CREATE TABLE IF NOT EXISTS subtasks (
  task_id TEXT NOT NULL,
  subtask_id TEXT NOT NULL,
  name TEXT NOT NULL,
  estimate_seconds INTEGER NOT NULL,
  weight DOUBLE PRECISION NOT NULL,
  dependencies_json JSONB NOT NULL,
  requires_decision BOOLEAN NOT NULL,
  assigned_agent_id TEXT,
  status TEXT NOT NULL,
  started_at DOUBLE PRECISION,
  finished_at DOUBLE PRECISION,
  actual_seconds DOUBLE PRECISION,
  PRIMARY KEY (task_id, subtask_id),
  FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decision_tickets (
  ticket_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  subtask_id TEXT NOT NULL,
  importance_level INTEGER NOT NULL,
  summary TEXT NOT NULL,
  impact TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  requires_pause BOOLEAN NOT NULL,
  status TEXT NOT NULL,
  created_at DOUBLE PRECISION NOT NULL,
  resolved_at DOUBLE PRECISION,
  resolution TEXT,
  checkpoint_ref TEXT,
  FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checkpoints (
  checkpoint_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  created_at DOUBLE PRECISION NOT NULL,
  reason TEXT NOT NULL,
  snapshot_json JSONB NOT NULL,
  FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS task_metrics (
  task_id TEXT PRIMARY KEY,
  planned_seconds INTEGER NOT NULL,
  actual_seconds DOUBLE PRECISION,
  absolute_error DOUBLE PRECISION,
  error_rate DOUBLE PRECISION,
  updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status_level ON decision_tickets(status, importance_level);
CREATE INDEX IF NOT EXISTS idx_subtasks_task_status ON subtasks(task_id, status);
CREATE INDEX IF NOT EXISTS idx_metrics_updated ON task_metrics(updated_at DESC);

-- pgvector preparation (Phase 2.1)
-- CREATE EXTENSION IF NOT EXISTS vector;
-- CREATE TABLE memory_vectors (
--   id BIGSERIAL PRIMARY KEY,
--   user_id TEXT NOT NULL,
--   task_id TEXT,
--   content TEXT NOT NULL,
--   embedding vector(1536) NOT NULL,
--   metadata JSONB NOT NULL DEFAULT '{}',
--   created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );
-- CREATE INDEX ON memory_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
