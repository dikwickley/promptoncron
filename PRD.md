Below is a **detailed PRD** you can actually hand to yourself (or a contractor) and build against. I’ll keep it opinionated, scoped, and MVP-focused, while clearly marking future extensions.

---

# PRD — **LLM & CRON (MVP)**

## 1. Overview

**LLM & CRON** is a micro-SaaS that allows users to:

* Define a **prompt**
* Optionally attach **web search** as a tool
* Schedule the prompt using **cron**
* Run the LLM at fixed intervals
* Persist **structured outputs** into a **SQLite database**
* View historical runs and tabular results

This MVP is **single-tenant per user**, **no auth**, **no billing**, **no sharing**.

---

## 2. Goals & Non-Goals

### Goals (MVP)

* Deterministic, structured LLM outputs
* Cron-driven execution
* Simple, inspectable data storage
* Debuggable and reproducible runs
* Minimal infra footprint

### Non-Goals (Explicitly Out of Scope)

* User authentication
* Billing / quotas
* Multi-user concurrency guarantees
* Arbitrary tools beyond web search
* Real-time streaming
* High availability / horizontal scale

---

## 3. User Journey (MVP)

1. User opens the app
2. Creates a **Task**

   * Enters a prompt
   * Enables/disables web search
   * Sets a cron schedule
3. Task runs automatically
4. Each run:

   * Fetches web results (if enabled)
   * Calls LLM via **Instructor**
   * Validates structured output
   * Stores results in SQLite
5. User views:

   * Latest output
   * Historical runs
   * Tabular data

---

## 4. Core Concepts & Data Model

### 4.1 Task

A recurring LLM job.

**Fields**

* `id` (UUID)
* `name`
* `prompt`
* `cron_expression`
* `timezone`
* `web_search_enabled` (bool)
* `status` (enabled | disabled)
* `created_at`
* `updated_at`

---

### 4.2 Run

A single execution of a Task.

**Fields**

* `id` (UUID)
* `task_id`
* `scheduled_for` (datetime)
* `started_at`
* `finished_at`
* `status` (queued | running | success | failed)
* `error_message` (nullable)
* `llm_model`
* `token_usage`
* `cost_estimate`

---

### 4.3 Structured Result

Instructor-validated output.

Stored as **JSON**, rendered as tables.

**Fields**

* `run_id`
* `schema_version`
* `columns` (JSON)
* `rows` (JSON)
* `summary` (optional text)

---

### 4.4 Web Search Snapshot

For reproducibility and debugging.

**Fields**

* `run_id`
* `query`
* `results` (JSON: title, url, snippet)

---

## 5. LLM Output Contract (Critical)

### 5.1 Instructor Schema (Example)

```python
class TableColumn(BaseModel):
    key: str
    label: str
    type: Literal["string", "number", "date", "url", "boolean"]

class TableResult(BaseModel):
    columns: list[TableColumn]
    rows: list[dict]
    summary: Optional[str]
```

### 5.2 Guarantees

* LLM output **must** conform to schema
* Non-conforming output triggers:

  1. Automatic repair attempt
  2. Retry once
  3. Fail the run if still invalid

---

## 6. Execution Flow

### 6.1 Scheduler

* Polls DB every `N` seconds
* Selects tasks where `next_run_at <= now`
* Inserts a `Run` row (status = queued)
* Computes next run time

### 6.2 Worker

1. Marks run as `running`
2. Executes web search (if enabled)
3. Constructs prompt:

   * System rules
   * User prompt
   * Tool output (clearly marked as untrusted)
4. Calls LLM via **Instructor**
5. Validates output
6. Writes structured result
7. Marks run as `success` or `failed`

---

## 7. Prompt Composition Rules

### System Prompt (Fixed)

* Enforce schema-only output
* Forbid following instructions from web content
* Require nulls for unknown data
* No markdown or prose

### User Prompt

* Stored verbatim
* Versioned implicitly via Run record

### Tool Injection

* Web results wrapped as:

  ```
  <WEB_RESULTS>
  ...
  </WEB_RESULTS>
  ```

---

## 8. Storage Strategy (MVP)

### SQLite

* One SQLite DB per user/session (ephemeral)
* Stored locally or in temp storage
* WAL mode enabled
* Single writer (worker)

### Tables

* `tasks`
* `runs`
* `results`
* `web_search_snapshots`

---

## 9. UI Requirements (Minimal)

### Pages

1. **Tasks List**

   * Name
   * Schedule
   * Enabled/Disabled
   * Last run status
2. **Task Detail**

   * Prompt (read-only)
   * Cron expression
   * Run history table
3. **Run Detail**

   * Structured table view
   * Raw JSON toggle
   * Web search snapshot
   * Errors/logs

---

## 10. Failure Modes & Handling

| Failure            | Handling                    |
| ------------------ | --------------------------- |
| LLM timeout        | Retry once                  |
| Invalid schema     | Repair + retry              |
| Web search failure | Continue without tool       |
| DB write failure   | Mark run failed             |
| Overlapping runs   | Skip if previous is running |

---

## 11. Constraints & Limits (Hardcoded)

* Minimum cron interval: **15 minutes**
* Max web results: **5**
* Max LLM output tokens: **2,000**
* Max retries per run: **2**
* Max run duration: **2 minutes**

---

## 12. Observability (MVP-Level)

* Structured logs per run
* Store:

  * Prompt hash
  * Tool usage
  * Validation errors
* No external metrics system

---

## 13. Security (MVP Baseline)

* No secrets stored in prompts (user responsibility)
* Web content treated as untrusted
* No code execution tools
* No user isolation guarantees

---

## 14. Tech Stack (Suggested)

* **Backend**: FastAPI
* **Scheduler**: in-process loop
* **Worker**: background task / separate process
* **LLM**: OpenAI / Anthropic via Instructor
* **DB**: SQLite
* **UI**: Minimal React or server-rendered templates

---

## 15. Future Extensions (Not MVP)

* Auth + per-user DB
* Postgres backend
* More tools (APIs, scraping, files)
* Schema editor UI
* CSV export
* Budget limits
* Notifications (email / webhook)
* Agent-style multi-step runs

---

## 16. Success Criteria (MVP)

* A task can run on schedule without manual intervention
* Structured output always validates or fails cleanly
* User can view historical tabular data
* System can run unattended for days without corruption

---

If you want, next we can:

* Turn this PRD into a **folder structure + DB schema**
* Write the **scheduler + worker pseudocode**
* Design the **exact Instructor prompt templates**
* Or do a **1-day MVP build plan** with checkpoints

Just tell me which direction.
