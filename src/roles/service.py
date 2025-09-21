from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from ..models import Role
from .schemas import RoleCreate, RoleUpdate, RoleResponse


class RoleService:
    @staticmethod
    async def get_roles(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[RoleResponse], int]:
        """Get paginated list of roles"""
        query = select(Role)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                Role.name.ilike(search_pattern) |
                Role.description.ilike(search_pattern)
            )

        # Get total count
        count_query = select(func.count(Role.id))
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                Role.name.ilike(search_pattern) |
                Role.description.ilike(search_pattern)
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(Role.name)
        result = await db.execute(query)
        roles = result.scalars().all()

        # Convert to response format
        role_responses = [
            RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                created_at=role.created_at,
                updated_at=role.updated_at
            )
            for role in roles
        ]

        return role_responses, total

    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        query = select(Role).where(Role.id == role_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_role_by_name(db: AsyncSession, name: str) -> Optional[Role]:
        """Get role by name"""
        query = select(Role).where(Role.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
        """Create a new role"""
        # Check if role already exists
        existing_role = await RoleService.get_role_by_name(db, role_data.name)
        if existing_role:
            raise ValueError("Role with this name already exists")

        role = Role(
            name=role_data.name,
            description=role_data.description
        )

        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def update_role(db: AsyncSession, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        """Update role"""
        role = await RoleService.get_role_by_id(db, role_id)
        if not role:
            return None

        # Check name uniqueness if updating name
        if role_data.name and role_data.name != role.name:
            existing_role = await RoleService.get_role_by_name(db, role_data.name)
            if existing_role:
                raise ValueError("Role with this name already exists")

        # Update fields
        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description

        await db.commit()
        await db.refresh(role)
        return role

    @staticmethod
    async def delete_role(db: AsyncSession, role_id: int) -> bool:
        """Delete role"""
        role = await RoleService.get_role_by_id(db, role_id)
        if not role:
            return False

        await db.delete(role)
        await db.commit()
        return True