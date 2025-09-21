from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from .service import RoleService
from .schemas import RoleCreate, RoleUpdate, RoleResponse, RoleListResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/", response_model=RoleListResponse)
async def get_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of roles with search functionality"""
    try:
        roles, total = await RoleService.get_roles(db, skip, limit, search)
        page = (skip // limit) + 1

        return RoleListResponse(
            roles=roles,
            total=total,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)):
    """Get role by ID"""
    role = await RoleService.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        created_at=role.created_at,
        updated_at=role.updated_at
    )


@router.post("/", response_model=RoleResponse)
async def create_role(role_data: RoleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new role"""
    try:
        role = await RoleService.create_role(db, role_data)
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update role"""
    try:
        role = await RoleService.update_role(db, role_id, role_data)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)):
    """Delete role"""
    success = await RoleService.delete_role(db, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")

    return {"message": "Role deleted successfully"}