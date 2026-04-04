import secrets
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.core.config import settings
from app.utils.email import send_otp_email


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    print("STEP 0: start")

    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=409, detail="Email exists")

    print("STEP 1: before hashing")

    hashed_password = get_password_hash(user_in.password[:72])

    print("STEP 2: after hashing")

    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True
    )

    print("STEP 3: before db add")

    db.add(user)
    db.commit()
    db.refresh(user)

    print("STEP 4: done")

    return user

    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=409, detail="Email exists")

    print("STEP 1: before hashing")

    safe_password = user_in.password[:72]

    hashed_password = get_password_hash(safe_password)

    print("STEP 2: after hashing")

    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True
    )

    print("STEP 3: before db add")

    db.add(user)
    db.commit()

    print("STEP 4: after commit")

    db.refresh(user)

    print("STEP 5: done")

    return user

    # 🔴 DEBUG (temporary)
    print("PASSWORD LENGTH:", len(user_in.password))
    print("PASSWORD VALUE:", user_in.password)

    # ✅ FIX: prevent bcrypt crash
    safe_password = user_in.password[:72]

    # hash password
    hashed_password = get_password_hash(safe_password)

    # create user
    user = User(
    email=user_in.email,
    hashed_password=hashed_password,
    full_name=user_in.full_name,   # ✅ ADD THIS
    is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Verify credentials and return user. Raises 401 on failure."""
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def generate_otp(db: Session, email: str) -> str:
    """Generate a 6-digit OTP, store hashed secret, email it."""
    user = get_user_by_email(db, email)
    if not user:
        # Return 200 anyway — don't leak whether email exists
        return "ok"

    otp = str(random.randint(100000, 999999))
    user.otp_secret = get_password_hash(otp)  # Hash the OTP too
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()

    # Fire and forget — email sending errors don't block the response
    try:
        send_otp_email(user.email, otp)
    except Exception:
        pass  # Log in production

    return "ok"


def verify_otp_and_reset(db: Session, email: str, otp: str, new_password: str) -> bool:
    """Verify OTP and update password."""
    user = get_user_by_email(db, email)
    if not user or not user.otp_secret or not user.otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    if datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")

    if not verify_password(otp, user.otp_secret):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    user.hashed_password = get_password_hash(new_password[:72])
    user.otp_secret = None
    user.otp_expires_at = None
    db.commit()
    return True


async def google_oauth_login(db: Session, code: str) -> tuple[User, str, str]:
    """Exchange Google auth code for user info, upsert user, return tokens."""
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google OAuth failed")

        google_tokens = token_resp.json()
        access_token = google_tokens.get("access_token")

        # Get user info from Google
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = userinfo_resp.json()

    google_id = userinfo.get("id")
    email = userinfo.get("email")
    name = userinfo.get("name")
    avatar = userinfo.get("picture")

    # Find existing user or create new one
    user = db.query(User).filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()

    if user:
        # Update Google fields if they logged in via email before
        user.google_id = google_id
        user.is_oauth_user = True
        user.avatar_url = avatar
        user.is_verified = True
    else:
        user = User(
            email=email,
            google_id=google_id,
            full_name=name,
            avatar_url=avatar,
            is_oauth_user=True,
            is_verified=True,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    return user, access, refresh


from app.schemas.user import UserResponse

def build_token_response(user: User) -> dict:
    print("STEP 6: building token")

    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }
