import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta
import httpx

from app.db import get_session
from app.models.models import (
    User,
    UserCreate,
    UserResponse,
    Token,
    UserSettings,
    utc_now,
)
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.config import settings
from app.core.rate_limit import limiter
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def get_token_expiry() -> "datetime":
    from datetime import datetime, timezone

    return datetime.now(timezone.utc) + timedelta(hours=24)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("20/minute")
async def register(
    request: Request, user_in: UserCreate, session: Session = Depends(get_session)
):
    existing_user = session.exec(
        select(User).where(User.email == user_in.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    verification_token = generate_verification_token()

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        auth_provider="email",
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=get_token_expiry(),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    user_settings = UserSettings(user_id=user.id)
    session.add(user_settings)
    session.commit()

    send_verification_email(user.email, verification_token)

    return user


@router.post("/verify")
async def verify_email(
    token: str = Query(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.verification_token == token)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    if user.verification_token_expires and utc_now() > user.verification_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new one.",
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    session.add(user)
    session.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
@limiter.limit("5/minute")
async def resend_verification(
    request: Request,
    email: str,
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == email)).first()

    if not user:
        return {"message": "If the email exists, a verification link has been sent"}

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    if user.auth_provider != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google login",
        )

    verification_token = generate_verification_token()
    user.verification_token = verification_token
    user.verification_token_expires = get_token_expiry()
    session.add(user)
    session.commit()

    send_verification_email(user.email, verification_token)

    return {"message": "If the email exists, a verification link has been sent"}


@router.post("/login", response_model=Token)
@limiter.limit("20/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.email == form_data.username)).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/google")
async def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured",
        )

    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.FRONTEND_URL}/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        "access_type=offline&"
        f"state={state}"
    )

    return {"auth_url": google_auth_url, "state": state}


@router.post("/google/callback", response_model=Token)
async def google_callback(
    code: str,
    session: Session = Depends(get_session),
):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login not configured",
        )

    redirect_uri = f"{settings.FRONTEND_URL}/auth/google/callback"

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token",
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google",
            )

        google_user = userinfo_response.json()

    google_id = google_user.get("id")
    email = google_user.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email",
        )

    user = session.exec(select(User).where(User.google_id == google_id)).first()

    if not user:
        user = session.exec(select(User).where(User.email == email)).first()

        if user:
            if user.auth_provider == "email" and user.hashed_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered with password. Please login with email/password.",
                )
            user.google_id = google_id
            user.auth_provider = "google"
            user.is_verified = True
            session.add(user)
            session.commit()
        else:
            user = User(
                email=email,
                google_id=google_id,
                auth_provider="google",
                is_verified=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            user_settings = UserSettings(user_id=user.id)
            session.add(user_settings)
            session.commit()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return Token(access_token=jwt_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
