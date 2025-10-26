from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.core.database.models.user import Role, User
from src.core.security import get_admin_user
from src.schemas.user import UserAdminCreate, UserAdminRead, UserListResponse, UserUpdate

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],  # All routes require admin
)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by email or username"),
    role: str | None = Query(None, description="Filter by role"),
    verified: bool | None = Query(None, description="Filter by verification status"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Get paginated list of all users with filtering options."""

    # Build query
    query = select(User)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where((User.email.ilike(search_term)) | (User.user_name.ilike(search_term)))

    if role:
        try:
            role_enum = Role[role.upper()]
            query = query.where(User.role == role_enum)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {role}. Must be 'user' or 'admin'"
            )

    if verified is not None:
        query = query.where(User.verified == verified)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        total=total, page=page, page_size=page_size, users=[UserAdminRead.model_validate(user) for user in users]
    )


@router.get("/users/{user_id}", response_model=UserAdminRead)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Get detailed information about a specific user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserAdminRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Update user information (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent admin from demoting themselves
    if user.id == current_admin.id and user_update.role and user_update.role.lower() != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own admin role")

    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "role":
            try:
                value = Role[value.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {value}. Must be 'user' or 'admin'"
                )
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return UserAdminRead.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Delete a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent admin from deleting themselves
    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    await db.delete(user)
    await db.commit()

    return None


@router.get("/stats")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Get user statistics for dashboard."""

    # Total users
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar_one()

    # Verified users
    verified_users_result = await db.execute(select(func.count(User.id)).where(User.verified))
    verified_users = verified_users_result.scalar_one()

    # Admin users
    admin_users_result = await db.execute(select(func.count(User.id)).where(User.role == Role.ADMIN))
    admin_users = admin_users_result.scalar_one()

    # Recent users (last 7 days)
    from datetime import datetime, timedelta

    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_users_result = await db.execute(select(func.count(User.id)).where(User.created_at >= seven_days_ago))
    recent_users = recent_users_result.scalar_one()

    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "unverified_users": total_users - verified_users,
        "admin_users": admin_users,
        "regular_users": total_users - admin_users,
        "recent_users": recent_users,
    }


@router.post("/users/bulk-action")
async def bulk_action_users(
    user_ids: list[UUID],
    action: str = Query(..., description="Action to perform: verify, unverify, promote, demote, delete"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Perform bulk actions on multiple users."""
    if not user_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user IDs provided")

    # Fetch users
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found with provided IDs")

    # Check if admin is trying to modify themselves
    admin_in_list = any(user.id == current_admin.id for user in users)

    updated_count = 0

    if action == "verify":
        for user in users:
            if not user.verified:
                user.verified = True
                updated_count += 1

    elif action == "unverify":
        for user in users:
            if user.verified and user.id != current_admin.id:
                user.verified = False
                updated_count += 1

    elif action == "promote":
        for user in users:
            if user.role != Role.ADMIN:
                user.role = Role.ADMIN
                updated_count += 1

    elif action == "demote":
        if admin_in_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself")
        for user in users:
            if user.role == Role.ADMIN:
                user.role = Role.USER
                updated_count += 1

    elif action == "delete":
        if admin_in_list:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
        for user in users:
            await db.delete(user)
            updated_count += 1

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid action: {action}")

    await db.commit()

    return {"success": True, "action": action, "updated_count": updated_count, "total_requested": len(user_ids)}


@router.post("/users", response_model=UserAdminRead)
async def create_user(
    user_data: UserAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Create a new user (admin only)."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    # Generate user_name if not provided
    user_name = user_data.user_name or user_data.email.split("@")[0]

    # Hash password
    from src.core.security import get_password_hash

    hashed_password = get_password_hash(user_data.password)

    # Create user
    new_user = User(
        user_name=user_name,
        email=str(user_data.email),
        password=hashed_password,
        role=Role[user_data.role.upper()],
        verified=user_data.verified,
        preferences=user_data.preferences,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserAdminRead.model_validate(new_user)
