import secrets
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session, select, func

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.api.billing import get_or_create_subscription
from app.models.models import (
    User,
    TeamMember,
    TeamRole,
    InviteStatus,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    utc_now,
)

router = APIRouter(prefix="/team", tags=["team"])


@router.get("/", response_model=List[TeamMemberResponse])
async def list_team_members(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    members = session.exec(
        select(TeamMember).where(TeamMember.team_owner_id == current_user.id)
    ).all()
    return members


@router.post("/invite", response_model=TeamMemberResponse, status_code=201)
@limiter.limit("10/minute")
async def invite_member(
    request: Request,
    data: TeamMemberCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    subscription = get_or_create_subscription(session, current_user)
    max_members = subscription.limits["team_members"]

    current_count = session.exec(
        select(func.count(TeamMember.id)).where(
            TeamMember.team_owner_id == current_user.id,
            TeamMember.invite_status != InviteStatus.DECLINED,
        )
    ).one()

    if current_count >= max_members:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Team member limit reached ({max_members}). Upgrade your plan to add more.",
        )

    existing = session.exec(
        select(TeamMember).where(
            TeamMember.team_owner_id == current_user.id,
            TeamMember.email == data.email,
            TeamMember.invite_status != InviteStatus.DECLINED,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email has already been invited.",
        )

    if data.email == current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot invite yourself.",
        )

    member = TeamMember(
        team_owner_id=current_user.id,
        email=data.email,
        role=data.role,
        invite_status=InviteStatus.PENDING,
        invite_token=secrets.token_urlsafe(32),
        invited_at=utc_now(),
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.post("/invite/{token}/accept", response_model=TeamMemberResponse)
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    member = session.exec(
        select(TeamMember).where(TeamMember.invite_token == token)
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found."
        )
    if member.invite_status != InviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite already {member.invite_status.value.lower()}.",
        )
    if member.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite is for a different email address.",
        )

    member.invite_status = InviteStatus.ACCEPTED
    member.user_id = current_user.id
    member.accepted_at = utc_now()
    member.invite_token = None
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.post("/invite/{token}/decline", response_model=TeamMemberResponse)
async def decline_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    member = session.exec(
        select(TeamMember).where(TeamMember.invite_token == token)
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found."
        )
    if member.invite_status != InviteStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite already {member.invite_status.value.lower()}.",
        )
    if member.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite is for a different email address.",
        )

    member.invite_status = InviteStatus.DECLINED
    member.invite_token = None
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def _get_member_with_permission(
    member_id: int,
    current_user: User,
    session: Session,
) -> TeamMember:
    member = session.exec(
        select(TeamMember).where(
            TeamMember.id == member_id,
            TeamMember.team_owner_id == current_user.id,
        )
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found."
        )
    return member


@router.put("/{member_id}", response_model=TeamMemberResponse)
async def update_member_role(
    member_id: int,
    data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    member = _get_member_with_permission(member_id, current_user, session)

    if member.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )
    if member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change the owner's role.",
        )

    if data.role is not None:
        member.role = data.role
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/{member_id}", status_code=204)
async def remove_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    member = _get_member_with_permission(member_id, current_user, session)

    if member.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself.",
        )
    if member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove the team owner.",
        )

    session.delete(member)
    session.commit()
