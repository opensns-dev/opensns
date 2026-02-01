from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import Asset

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/campaign/{campaign_id}", response_model=List[Asset])
async def list_assets(campaign_id: int, session: Session = Depends(get_session)):
    assets = session.exec(select(Asset).where(Asset.campaign_id == campaign_id)).all()
    return assets


@router.get("/{asset_id}", response_model=Asset)
async def get_asset(asset_id: int, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
