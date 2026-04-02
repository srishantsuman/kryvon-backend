from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.session import get_db
from app.schemas.user import (
    UserCreate, LoginRequest, TokenResponse, UserResponse,
    OTPRequest, OTPVerify, GoogleOAuthRequest
)
from app.services import auth_service
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(user_in: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = auth_service.create_user(db, user_in)
    tokens = auth_service.build_token_response(user)

    # Set refresh token as httpOnly cookie — never exposed to JS
    response.set_cookie(
        key="refresh_token",
        value=create_refresh_token(user.id),
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(login_in: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, login_in.email, login_in.password)
    tokens = auth_service.build_token_response(user)

    response.set_cookie(
        key="refresh_token",
        value=create_refresh_token(user.id),
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, db: Session = Depends(get_db)):
    """Use refresh token from cookie to get a new access token."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError()
        user_id = int(payload["sub"])
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return auth_service.build_token_response(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(otp_req: OTPRequest, db: Session = Depends(get_db)):
    auth_service.generate_otp(db, otp_req.email)
    return {"message": "If this email exists, a reset code has been sent"}


@router.post("/reset-password")
def reset_password(otp_verify: OTPVerify, db: Session = Depends(get_db)):
    auth_service.verify_otp_and_reset(db, otp_verify.email, otp_verify.otp, otp_verify.new_password)
    return {"message": "Password reset successfully"}


@router.post("/google", response_model=TokenResponse)
async def google_login(req: GoogleOAuthRequest, response: Response, db: Session = Depends(get_db)):
    user, access, refresh = await auth_service.google_oauth_login(db, req.code)

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    from app.schemas.user import UserResponse as UR
    return {"access_token": access, "token_type": "bearer", "user": user}
