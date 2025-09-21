from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from .service import UserService
from .schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserRoleAssignment, UserRoleRemoval
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of users with search functionality"""
    try:
        users, total = await UserService.get_users(db, skip, limit, search)
        page = (skip // limit) + 1

        return UserListResponse(
            users=users,
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID with roles"""
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles = [ur.role.name for ur in user.user_roles if ur.role]
    return UserResponse(
        id=user.id,
        name=user.name,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        roles=roles
    )


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user"""
    try:
        user = await UserService.create_user(db, user_data)
        return UserResponse(
            id=user.id,
            name=user.name,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update user"""
    try:
        user = await UserService.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        roles = [ur.role.name for ur in user.user_roles if ur.role]
        return UserResponse(
            id=user.id,
            name=user.name,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=roles
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete user"""
    success = await UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


@router.post("/assign-role")
async def assign_role_to_user(
    assignment: UserRoleAssignment,
    db: AsyncSession = Depends(get_db)
):
    """Assign role to user"""
    try:
        await UserService.assign_role(db, assignment.user_id, assignment.role_id)
        return {"message": "Role assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remove-role")
async def remove_role_from_user(
    removal: UserRoleRemoval,
    db: AsyncSession = Depends(get_db)
):
    """Remove role from user"""
    success = await UserService.remove_role(db, removal.user_id, removal.role_id)
    if not success:
        raise HTTPException(status_code=404, detail="User role assignment not found")

    return {"message": "Role removed successfully"}


@router.post("/{user_id}/roles")
async def assign_role_to_user_alt(
    user_id: int,
    role_assignment: dict,
    db: AsyncSession = Depends(get_db)
):
    """Assign role to user (alternative endpoint for frontend)"""
    try:
        role_id = role_assignment.get('role_id')
        if not role_id:
            raise HTTPException(status_code=400, detail="role_id is required")

        await UserService.assign_role(db, user_id, role_id)
        return {"success": True, "message": "Role assigned successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user_alt(
    user_id: int,
    role_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove role from user (alternative endpoint for frontend)"""
    success = await UserService.remove_role(db, user_id, role_id)
    if not success:
        return {"success": False, "message": "User role assignment not found"}

    return {"success": True, "message": "Role removed successfully"}