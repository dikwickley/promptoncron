from __future__ import annotations

import argparse
import sys

import uvicorn

from app.database import ENGINE
from app.models import Base
from app.services.scheduler import run_scheduler_loop
from app.services.worker import run_worker_loop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="promptoncron")
    sub = parser.add_subparsers(dest="cmd", required=True)

    api_p = sub.add_parser("api")
    api_p.add_argument("--host", default="0.0.0.0")
    api_p.add_argument("--port", type=int, default=8000)

    sub.add_parser("scheduler")
    sub.add_parser("worker")

    args = parser.parse_args(argv)

    # Ensure tables exist for any process (api/scheduler/worker).
    Base.metadata.create_all(bind=ENGINE)

    if args.cmd == "api":
        uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False)
        return 0

    if args.cmd == "scheduler":
        run_scheduler_loop()
        return 0

    if args.cmd == "worker":
        run_worker_loop()
        return 0

    raise RuntimeError(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


