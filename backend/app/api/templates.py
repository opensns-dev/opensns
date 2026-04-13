import json
from typing import Any, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.db import get_session
from app.models.models import (
    Template,
    TemplateIndustry,
    TemplatePlatform,
    TemplateResponse,
    User,
)

router = APIRouter(prefix="/templates", tags=["templates"])


def _to_response(t: Template) -> TemplateResponse:
    return TemplateResponse(
        id=cast(int, t.id),
        name=t.name,
        description=t.description,
        industry=t.industry,
        platform=t.platform,
        layout=t.layout,
        copy_template=json.loads(t.copy_template) if t.copy_template else {},
        style_config=json.loads(t.style_config) if t.style_config else {},
        preview_url=t.preview_url,
        is_active=t.is_active,
    )


@router.get("/industries", response_model=List[str])
async def list_industries(
    _current_user: User = Depends(get_current_user),
):
    return [i.value for i in TemplateIndustry]


@router.get("/platforms", response_model=List[str])
async def list_platforms(
    _current_user: User = Depends(get_current_user),
):
    return [p.value for p in TemplatePlatform]


@router.get("/", response_model=List[TemplateResponse])
@limiter.limit("30/minute")
async def list_templates(
    request: Request,
    industry: Optional[TemplateIndustry] = None,
    platform: Optional[TemplatePlatform] = None,
    _current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    stmt = select(Template).where(Template.is_active == True)

    if industry:
        stmt = stmt.where(Template.industry == industry)
    if platform:
        stmt = stmt.where(Template.platform == platform)

    stmt = stmt.order_by(cast(Any, Template.sort_order), cast(Any, Template.id))
    templates = session.exec(stmt).all()
    return [_to_response(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    _current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    template = session.exec(
        select(Template).where(Template.id == template_id, Template.is_active == True)
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return _to_response(template)
