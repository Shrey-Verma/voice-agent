-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id text PRIMARY KEY,
    name text NOT NULL,
    version integer NOT NULL,
    json jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- Runs table
CREATE TABLE IF NOT EXISTS runs (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id text NOT NULL REFERENCES workflows(id),
    status text NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    variables jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT runs_finished_at_check CHECK (
        (status IN ('completed', 'failed') AND finished_at IS NOT NULL) OR
        (status IN ('pending', 'running') AND finished_at IS NULL)
    )
);

-- Run steps table
CREATE TABLE IF NOT EXISTS run_steps (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id uuid NOT NULL REFERENCES runs(id),
    node_id text NOT NULL,
    input jsonb NOT NULL DEFAULT '{}'::jsonb,
    output jsonb NOT NULL DEFAULT '{}'::jsonb,
    variables_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    latency_ms integer,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id uuid REFERENCES runs(id),
    level text NOT NULL CHECK (level IN ('INFO', 'WARNING', 'ERROR')),
    message text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflows(name);
CREATE INDEX IF NOT EXISTS idx_runs_workflow_id ON runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_run_steps_run_id ON run_steps(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_run_id ON audit_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_level ON audit_logs(level);

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
