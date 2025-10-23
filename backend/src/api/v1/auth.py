from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import timedelta

from src.core.database.database import get_db
from src.core.database.models.user import User
from src.core.security import create_access_token, get_current_user, get_password_hash, verify_password, get_verified_user
from src.core.decorator.timer import timer
from src.schemas.user import UserCreate, UserRead
from src.settings.env import settings
from src.domains.use_cases.verification import VerificationUseCase, get_verification_usecase

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Error messages as simple strings
class ResponseMessage:
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_TOKEN = "Invalid token"
    INVALID_PASSWORD_FORMAT = "Invalid password storage format"
    INCORRECT_EMAIL_OR_PASSWORD = "Incorrect email or password"
    VERIFICATION_EMAIL_SENT = "Verification email sent successfully"
    RATE_LIMIT_EXCEEDED = "Too many verification requests. Please try again later."

@router.post("/login", response_model=Token)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_in.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_in.password, str(user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResponseMessage.INCORRECT_EMAIL_OR_PASSWORD,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserRead)
@timer
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase)
):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    if user:
        raise HTTPException(
            status_code=400,
            detail=ResponseMessage.EMAIL_ALREADY_REGISTERED
        )

    print("Registering user:", user_in.email, user_in.password)
    user_name = str(user_in.email).split("@")[0]
    hashed_password = get_password_hash(user_in.password)
    new_user = User(user_name=user_name, email=str(user_in.email), password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Send verification email with user information
    try:
        job_id = await verification_use_case.send_email_verification(
            email=new_user.email,
            user_name=user_name,
            user_email=new_user.email,
            expiry_hours=24,
            company_name=settings.EMAILS_FROM_NAME or "BTL_OOP_PTIT",
            custom_message="Welcome to our platform! Please verify your email to unlock all features.",
        )
        print(f"Verification email queued with job ID: {job_id}")
    except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send verification email: {e}")
        if "Too many requests" in str(e):
            # Optionally inform user about rate limiting
            pass

    return UserRead.model_validate(new_user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.user_name == form_data.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResponseMessage.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResponseMessage.INCORRECT_EMAIL_OR_PASSWORD,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_verified_user)):
    return UserRead.model_validate(current_user)
