from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import get_settings
from app.database import db_session
from app.models import Run, Task
from app.utils.cron import compute_next_run_at


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enqueue_run(task_id: str) -> None:
    now = _utcnow()
    with db_session() as s:
        task = s.get(Task, task_id)
        if not task or task.status != "enabled":
            return

        # Enqueue a run at "now" (APScheduler guarantees schedule; we record scheduled_for for debugging).
        s.add(Run(task_id=task.id, scheduled_for=now, status="queued"))

        # Keep next_run_at roughly accurate for UI.
        try:
            task.next_run_at = compute_next_run_at(
                cron_expression=task.cron_expression,
                timezone=task.timezone,
                base_time_utc=now,
            )
        except Exception:
            task.next_run_at = None


def _sync_jobs(scheduler: BlockingScheduler) -> None:
    """
    Reconcile DB tasks -> APScheduler jobs so task edits take effect without restarts.
    """
    with db_session() as s:
        tasks = s.execute(select(Task)).scalars().all()

    desired: dict[str, Task] = {t.id: t for t in tasks if t.status == "enabled"}
    existing_ids = {job.id for job in scheduler.get_jobs()}

    # Remove jobs for disabled/deleted tasks
    for job_id in list(existing_ids):
        if job_id not in desired:
            scheduler.remove_job(job_id)

    # Add or update jobs for enabled tasks
    for task_id, task in desired.items():
        try:
            tz = ZoneInfo(task.timezone)
            trigger = CronTrigger.from_crontab(task.cron_expression, timezone=tz)
        except Exception:
            # Invalid cron/timezone in DB: skip scheduling, leave task as-is.
            continue

        if task_id not in existing_ids:
            scheduler.add_job(_enqueue_run, trigger=trigger, args=[task_id], id=task_id, max_instances=1)
        else:
            # Update trigger if changed
            scheduler.reschedule_job(task_id, trigger=trigger)


def run_scheduler_loop() -> None:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=ZoneInfo("UTC"))

    # Initial sync and periodic reconciliation.
    _sync_jobs(scheduler)
    scheduler.add_job(
        _sync_jobs,
        trigger="interval",
        seconds=max(5, int(settings.scheduler_interval)),
        args=[scheduler],
        id="_sync_jobs",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()


