from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.database.database import get_db
from src.core.database.models.user import User
from src.core.decorator.timer import timer
from src.core.security import create_access_token, get_password_hash, get_verified_user, verify_password
from src.domains.verification.use_cases import VerificationUseCase, get_verification_usecase
from src.schemas.user import UserCreate, UserRead
from src.settings.env import settings

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

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str

class VerifyEmailResponse(BaseModel):
    success: bool
    message: str
    remaining_attempts: int | None = None

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ResendVerificationResponse(BaseModel):
    success: bool
    message: str

class AuthResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    user: UserRead

# Error messages as simple strings
class ResponseMessage:
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_TOKEN = "Invalid token"
    INVALID_PASSWORD_FORMAT = "Invalid password storage format"
    INCORRECT_EMAIL_OR_PASSWORD = "Incorrect email or password"
    VERIFICATION_EMAIL_SENT = "Verification email sent successfully"
    RATE_LIMIT_EXCEEDED = "Too many use_cases requests. Please try again later."

@router.post("/login", response_model=AuthResponse)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login_in.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_in.password, str(user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ResponseMessage.INCORRECT_EMAIL_OR_PASSWORD,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email before logging in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "user": UserRead.model_validate(user)
    }


@router.post("/register", response_model=AuthResponse)
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

    # Send use_cases email with user information
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
        print(f"Failed to send use_cases email: {e}")
        if "Too many requests" in str(e):
            # Optionally inform user about rate limiting
            pass

    return {"user": UserRead.model_validate(new_user)}


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



@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase)
):
    """
    Verify user's email with use_cases code.

    Args:
        request: Contains email and use_cases code
        db: Database session
        verification_use_case: Verification use case for code validation

    Returns:
        VerifyEmailResponse with success status and message

    Raises:
        HTTPException: If user not found or code is invalid
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already verified
    if user.verified:
        return VerifyEmailResponse(
            success=True,
            message="Email is already verified"
        )

    # Verify the code
    verification_result = await verification_use_case.verify_email(
        email=str(request.email),
        code=request.code
    )

    if not verification_result["valid"]:
        remaining = verification_result.get("remaining_attempts")

        if remaining is not None and remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid use_cases code. {remaining} attempts remaining."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired use_cases code. Please request a new one."
            )

    # Update user's verified status
    user.verified = True
    await db.commit()
    await db.refresh(user)

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully"
    )


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase)
):
    """
    Resend use_cases email to user.

    Args:
        request: Contains user email
        db: Database session
        verification_use_case: Verification use case

    Returns:
        ResendVerificationResponse with success status

    Raises:
        HTTPException: If user not found, already verified, or rate limited
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already verified
    if user.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )

    # Send use_cases email
    try:
        job_id = await verification_use_case.send_email_verification(
            email=user.email,
            user_name=user.user_name,
            user_email=user.email,
            expiry_hours=24,
            company_name=settings.EMAILS_FROM_NAME or "BTL_OOP_PTIT",
            custom_message="Please verify your email to unlock all features.",
        )
        print(f"Verification email queued with job ID: {job_id}")

        return ResendVerificationResponse(
            success=True,
            message="Verification email sent successfully"
        )
    except Exception as e:
        error_msg = str(e)
        if "Too many requests" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ResponseMessage.RATE_LIMIT_EXCEEDED
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send use_cases email: {error_msg}"
        )
