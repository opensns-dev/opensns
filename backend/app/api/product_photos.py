import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from app.db import get_session
from app.models.models import (
    ProductPhoto,
    ProductPhotoCreate,
    ProductPhotoResponse,
    ProductPhotoStatus,
    User,
    utc_now,
)
from app.core.auth import get_current_user
from app.core.rate_limit import limiter
from app.services.usage import check_product_photo_credits, use_product_photo_credits

router = APIRouter(prefix="/product-photos", tags=["product-photos"])


def _to_response(photo: ProductPhoto) -> ProductPhotoResponse:
    try:
        angles = json.loads(photo.angles) if photo.angles else []
    except (json.JSONDecodeError, TypeError):
        angles = []
    try:
        results = json.loads(photo.results) if photo.results else []
    except (json.JSONDecodeError, TypeError):
        results = []
    return ProductPhotoResponse(
        id=photo.id,  # type: ignore[arg-type]
        user_id=photo.user_id,
        campaign_id=photo.campaign_id,
        original_image_url=photo.original_image_url,
        bg_removed_url=photo.bg_removed_url,
        status=photo.status,
        angles=angles,
        results=results,
        scene_prompt=photo.scene_prompt,
        error=photo.error,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
    )


@router.get("/", response_model=list[ProductPhotoResponse])
@limiter.limit("60/minute")
async def list_product_photos(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 20,
):
    statement = (
        select(ProductPhoto)
        .where(ProductPhoto.user_id == current_user.id)
        .order_by(ProductPhoto.created_at.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    )
    photos = session.exec(statement).all()
    return [_to_response(p) for p in photos]


@router.get("/{photo_id}", response_model=ProductPhotoResponse)
@limiter.limit("60/minute")
async def get_product_photo(
    photo_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    photo = session.get(ProductPhoto, photo_id)
    if not photo or photo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Product photo not found")
    return _to_response(photo)


@router.post("/", response_model=ProductPhotoResponse, status_code=201)
@limiter.limit("10/minute")
async def create_product_photo(
    photo_in: ProductPhotoCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    check_product_photo_credits(session, current_user, len(photo_in.angles))

    photo = ProductPhoto(
        user_id=current_user.id,  # type: ignore[arg-type]
        campaign_id=photo_in.campaign_id,
        original_image_url=photo_in.original_image_url,
        angles=json.dumps([a.value for a in photo_in.angles]),
        scene_prompt=photo_in.scene_prompt,
        status=ProductPhotoStatus.PENDING,
    )
    session.add(photo)

    use_product_photo_credits(
        session,
        current_user,
        len(photo_in.angles),
        photo_in.campaign_id,  # type: ignore[arg-type]
    )

    session.refresh(photo)
    return _to_response(photo)


@router.delete("/{photo_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_product_photo(
    photo_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    photo = session.get(ProductPhoto, photo_id)
    if not photo or photo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Product photo not found")
    session.delete(photo)
    session.commit()


@router.post("/{photo_id}/retry", response_model=ProductPhotoResponse)
@limiter.limit("10/minute")
async def retry_product_photo(
    photo_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    photo = session.get(ProductPhoto, photo_id)
    if not photo or photo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Product photo not found")
    if photo.status != ProductPhotoStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

    photo.status = ProductPhotoStatus.PENDING
    photo.error = None
    photo.results = "[]"
    photo.updated_at = utc_now()
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return _to_response(photo)
