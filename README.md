# `PromptOnCron`

![Screenshot](/assets/screenshot.png)


## What this is
`promptoncron` is a small “LLM + cron” app:
- Create a scheduled task (cron + prompt)
- Scheduler enqueues runs
- Worker executes runs and stores structured results in SQLite
- UI lets you browse tasks, runs, and tabular results

## How to run

### Prereqs
- Docker Desktop (or Docker Engine) with Docker Compose

### Configure env
- Edit `example.env` and set at least one provider key:
  - `OPENAI_API_KEY=...` and `LLM_PROVIDER=openai`
  - or `GEMINI_API_KEY=...` and `LLM_PROVIDER=gemini`
  - or `DEEPSEEK_API_KEY=...` and `LLM_PROVIDER=deepseek`

### Start

```bash
docker compose up -d --build --force-recreate
```

### Open
- UI: `http://localhost:3000`
- API health: `http://localhost:8000/healthz`
- API docs: `http://localhost:8000/docs`

---

### Services
- `api`: FastAPI backend (also serves DB schema creation on startup)
- `scheduler`: APScheduler reconciles DB tasks → cron jobs and enqueues runs
- `worker`: claims queued runs, calls the LLM, stores results
- `frontend`: React/Vite UI

### Storage
- SQLite file is stored in `./data/promptoncron.db` (bind-mounted into containers).

### LLM providers
Configured via `example.env`:
- `LLM_PROVIDER=openai` (uses `DEFAULT_LLM_MODEL`, e.g. `gpt-4o-mini` / `gpt-5-nano`)
- `LLM_PROVIDER=gemini` (uses `DEFAULT_LLM_MODEL`, e.g. `gemini-2.5-flash`)
- `LLM_PROVIDER=deepseek` (uses `DEFAULT_LLM_MODEL`, e.g. `deepseek-chat`)

### Common commands
- **Follow logs**:

```bash
docker compose logs -f api worker scheduler frontend
```

- **Reset DB** (destroys history):

```bash
rm -f ./data/promptoncron.db
docker compose up -d --build --force-recreate
```


