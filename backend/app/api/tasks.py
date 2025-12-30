from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Run, Task
from app.schemas import RunOut, TaskCreate, TaskOut, TaskUpdate
from app.utils.cron import compute_next_run_at, ensure_min_cron_interval_minutes


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _validate_timezone(tz: str) -> None:
    try:
        ZoneInfo(tz)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid timezone: {tz}") from e


@router.get("", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)) -> list[Task]:
    return db.execute(select(Task).order_by(desc(Task.created_at))).scalars().all()


@router.post("", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    now = _utcnow()
    _validate_timezone(payload.timezone)
    try:
        ensure_min_cron_interval_minutes(
            cron_expression=payload.cron_expression,
            timezone=payload.timezone,
            base_time_utc=now,
            min_minutes=15,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    task = Task(
        name=payload.name,
        prompt=payload.prompt,
        cron_expression=payload.cron_expression,
        timezone=payload.timezone,
        web_search_enabled=payload.web_search_enabled,
        status=payload.status,
    )

    if payload.status == "enabled":
        task.next_run_at = compute_next_run_at(
            cron_expression=payload.cron_expression,
            timezone=payload.timezone,
            base_time_utc=now,
        )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _utcnow()

    if payload.timezone is not None:
        _validate_timezone(payload.timezone)

    # Apply updates
    for field in ["name", "prompt", "cron_expression", "timezone", "web_search_enabled", "status"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(task, field, val)

    # Validate cron interval using the current (possibly updated) values.
    try:
        ensure_min_cron_interval_minutes(
            cron_expression=task.cron_expression,
            timezone=task.timezone,
            base_time_utc=now,
            min_minutes=15,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if task.status == "enabled":
        task.next_run_at = compute_next_run_at(
            cron_expression=task.cron_expression,
            timezone=task.timezone,
            base_time_utc=now,
        )
    else:
        task.next_run_at = None

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)) -> dict:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.post("/{task_id}/run", response_model=RunOut)
def trigger_run(task_id: str, db: Session = Depends(get_db)) -> Run:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = _utcnow()
    run = Run(task_id=task.id, scheduled_for=now, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/{task_id}/runs", response_model=list[RunOut])
def list_task_runs(task_id: str, db: Session = Depends(get_db)) -> list[Run]:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return (
        db.execute(select(Run).where(Run.task_id == task_id).order_by(desc(Run.scheduled_for)).limit(200))
        .scalars()
        .all()
    )


