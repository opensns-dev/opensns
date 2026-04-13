from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import WaitlistEntry, WaitlistRequest, WaitlistResponse, User
from app.core.auth import get_current_user
from app.core.rate_limit import limiter

router = APIRouter(prefix="/waitlist", tags=["waitlist"])


@router.post("/", response_model=WaitlistResponse)
@limiter.limit("5/minute")
async def join_waitlist(
    request: Request,
    data: WaitlistRequest,
    session: Session = Depends(get_session),
):
    existing = session.exec(
        select(WaitlistEntry).where(WaitlistEntry.email == data.email)
    ).first()
    if existing:
        return existing

    entry = WaitlistEntry(email=data.email)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/", response_model=list[WaitlistResponse])
async def list_waitlist(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    entries = session.exec(
        select(WaitlistEntry).order_by(WaitlistEntry.created_at.desc())
    ).all()
    return entries
