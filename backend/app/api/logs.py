from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import AgentLog

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/campaign/{campaign_id}", response_model=List[AgentLog])
async def list_logs(campaign_id: int, session: Session = Depends(get_session)):
    logs = session.exec(
        select(AgentLog).where(AgentLog.campaign_id == campaign_id)
    ).all()
    return logs
