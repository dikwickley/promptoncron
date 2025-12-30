from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Result, Run, WebSearchSnapshot
from app.schemas.result import ResultOut


router = APIRouter(prefix="/api", tags=["results"])


@router.get("/runs/{run_id}/result", response_model=ResultOut)
def get_result(run_id: str, db: Session = Depends(get_db)) -> Result:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    result = db.query(Result).filter(Result.run_id == run_id).one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/runs/{run_id}/web_search_snapshot")
def get_web_search_snapshot(run_id: str, db: Session = Depends(get_db)) -> dict:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    snap = db.query(WebSearchSnapshot).filter(WebSearchSnapshot.run_id == run_id).one_or_none()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {"run_id": run_id, "query": snap.query, "results": snap.results}


