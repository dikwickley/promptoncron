export type TaskStatus = "enabled" | "disabled";

export type Task = {
  id: string;
  name: string;
  prompt: string;
  cron_expression: string;
  timezone: string;
  web_search_enabled: boolean;
  status: TaskStatus;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
};

export type RunStatus = "queued" | "running" | "success" | "failed";

export type Run = {
  id: string;
  task_id: string;
  scheduled_for: string;
  started_at: string | null;
  finished_at: string | null;
  status: RunStatus;
  error_message: string | null;
  llm_model: string | null;
  token_usage: Record<string, unknown> | null;
  cost_estimate: number | null;
  created_at: string;
  updated_at: string;
};

export type ResultColumnType = "string" | "number" | "date" | "url" | "boolean";

export type ResultColumn = {
  key: string;
  label: string;
  type: ResultColumnType;
};

export type Result = {
  id: string;
  run_id: string;
  schema_version: number;
  columns: ResultColumn[];
  rows: Record<string, unknown>[];
  summary: string | null;
  created_at: string;
  updated_at: string;
};


