from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import desc, select, text

from app.config import get_settings
from app.database import db_session
from app.models import Result, Run, Task, WebSearchSnapshot
from app.prompts.templates import SYSTEM_PROMPT, build_user_prompt, wrap_web_results
from app.services.llm import generate_structured_table, stringify_for_web_results
from app.services.web_search import WebSearchError, tavily_search
from tenacity import RetryError


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _single_line(msg: str) -> str:
    # Keep API JSON valid + UI readable (no raw newlines/control chars).
    msg = (msg or "").replace("\r", " ").replace("\n", " ")
    # Collapse repeated whitespace
    return " ".join(msg.split())


def _claim_next_run_id() -> str | None:
    """
    Single-worker MVP: claim the oldest queued run.
    """
    with db_session() as s:
        run_id = s.execute(select(Run.id).where(Run.status == "queued").order_by(Run.scheduled_for).limit(1)).scalar()
        if not run_id:
            return None

        run = s.get(Run, run_id)
        if not run or run.status != "queued":
            return None

        # Overlap protection: if any run for this task is already running, skip this one.
        already_running = (
            s.execute(select(Run.id).where(Run.task_id == run.task_id).where(Run.status == "running").limit(1)).scalar()
            is not None
        )
        if already_running:
            run.status = "failed"
            run.error_message = "Skipped due to overlapping run"
            run.finished_at = _utcnow()
            s.add(run)
            return None

        run.status = "running"
        run.started_at = _utcnow()
        s.add(run)
        return run_id


def _finish_failed(*, run_id: str, error: str) -> None:
    with db_session() as s:
        run = s.get(Run, run_id)
        if not run:
            return
        run.status = "failed"
        # Never leak secrets in error messages (LLM client libs sometimes echo auth headers / keys).
        msg = _single_line(error)
        for secret in [get_settings().openai_api_key, get_settings().gemini_api_key, get_settings().tavily_api_key, getattr(get_settings(), "deepseek_api_key", None)]:
            if secret:
                msg = msg.replace(secret, "***REDACTED***")
        run.error_message = msg
        run.finished_at = _utcnow()
        s.add(run)


def _finish_success(*, run_id: str, result_columns: list[dict], result_rows: list[dict], summary: str | None, llm_model: str | None, token_usage: dict | None) -> None:
    with db_session() as s:
        run = s.get(Run, run_id)
        if not run:
            return
        run.status = "success"
        run.finished_at = _utcnow()
        run.llm_model = llm_model
        run.token_usage = token_usage
        s.add(run)

        s.add(
            Result(
                run_id=run_id,
                schema_version=1,
                columns=result_columns,
                rows=result_rows,
                summary=summary,
            )
        )


def _maybe_do_web_search(
    *,
    run_id: str,
    task_name: str,
    task_prompt: str,
    web_search_enabled: bool,
) -> str | None:
    if not web_search_enabled:
        return None

    # Simple heuristic: use task name as query; fall back to prompt prefix.
    query = (task_name or "").strip() or task_prompt.strip().splitlines()[0][:200]
    try:
        results = tavily_search(query=query, max_results=5)
    except WebSearchError:
        return None
    except Exception:
        return None

    with db_session() as s:
        s.add(WebSearchSnapshot(run_id=run_id, query=query, results=results))

    return wrap_web_results(stringify_for_web_results(results))


def _execute_run(run_id: str) -> None:
    try:
        # Load immutable task data (avoid passing ORM objects across sessions).
        with db_session() as s:
            run = s.get(Run, run_id)
            if not run:
                return
            task = s.get(Task, run.task_id)
            if not task:
                _finish_failed(run_id=run_id, error="Task not found")
                return
            task_data = {
                "id": task.id,
                "name": task.name,
                "prompt": task.prompt,
                "web_search_enabled": task.web_search_enabled,
            }

        web_block = _maybe_do_web_search(
            run_id=run_id,
            task_name=task_data["name"],
            task_prompt=task_data["prompt"],
            web_search_enabled=bool(task_data["web_search_enabled"]),
        )
        user_prompt = build_user_prompt(user_prompt=task_data["prompt"], web_results_block=web_block)

        try:
            table, token_usage, llm_model = generate_structured_table(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                task_name=task_data["name"],
            )
        except RetryError as e:
            # tenacity wraps the underlying exception; expose it for debugging.
            last = getattr(e, "last_attempt", None)
            underlying = None
            if last is not None:
                try:
                    underlying = last.exception()
                except Exception:
                    underlying = None
            msg = str(underlying or e)
            raise RuntimeError(f"LLM failed: {msg}") from underlying or e

        cols = [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in table.columns]  # type: ignore[arg-type]
        rows = list(table.rows)
        _finish_success(
            run_id=run_id,
            result_columns=cols,
            result_rows=rows,
            summary=table.summary,
            llm_model=llm_model,
            token_usage=token_usage,
        )
    except Exception as e:
        _finish_failed(run_id=run_id, error=f"Worker crashed: {e}")


def run_worker_loop() -> None:
    """
    MVP worker stub.

    Real implementation will:
    - claim queued runs atomically
    - execute web search (optional)
    - call LLM via Instructor
    - persist results
    """
    settings = get_settings()
    poll = max(1, int(settings.worker_poll_interval))

    while True:
        run_id = _claim_next_run_id()
        if run_id:
            _execute_run(run_id)

        time.sleep(poll)


