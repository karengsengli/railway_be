from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from typing import List, Optional
from passlib.context import CryptContext

from ..models import User, Role, UserHasRole
from .schemas import UserCreate, UserUpdate, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[UserResponse], int]:
        """Get paginated list of users with their roles"""
        query = select(User).options(selectinload(User.user_roles).selectinload(UserHasRole.role))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                User.name.ilike(search_pattern) |
                User.first_name.ilike(search_pattern) |
                User.last_name.ilike(search_pattern) |
                User.email.ilike(search_pattern) |
                User.phone.ilike(search_pattern)
            )

        # Get total count
        count_query = select(func.count(User.id))
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                User.name.ilike(search_pattern) |
                User.first_name.ilike(search_pattern) |
                User.last_name.ilike(search_pattern) |
                User.email.ilike(search_pattern) |
                User.phone.ilike(search_pattern)
            )

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(User.name)
        result = await db.execute(query)
        users = result.scalars().all()

        # Convert to response format with roles
        user_responses = []
        for user in users:
            roles = [ur.role.name for ur in user.user_roles if ur.role]
            user_response = UserResponse(
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
            user_responses.append(user_response)

        return user_responses, total

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID with roles"""
        query = select(User).options(selectinload(User.user_roles).selectinload(UserHasRole.role)).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = await UserService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password and create user
        hashed_password = UserService.hash_password(user_data.password)

        user = User(
            name=user_data.name,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            is_active=user_data.is_active,
            password=hashed_password
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None

        # Check email uniqueness if updating email
        if user_data.email and user_data.email != user.email:
            existing_user = await UserService.get_user_by_email(db, user_data.email)
            if existing_user:
                raise ValueError("User with this email already exists")

        # Update fields
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.password is not None:
            user.password = UserService.hash_password(user_data.password)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """Delete user"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False

        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def assign_role(db: AsyncSession, user_id: int, role_id: int) -> bool:
        """Assign role to user"""
        # Check if user exists
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")

        # Check if role exists
        role_query = select(Role).where(Role.id == role_id)
        role_result = await db.execute(role_query)
        role = role_result.scalar_one_or_none()
        if not role:
            raise ValueError("Role not found")

        # Check if assignment already exists
        existing_query = select(UserHasRole).where(
            UserHasRole.user_id == user_id,
            UserHasRole.role_id == role_id
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise ValueError("User already has this role")

        # Create assignment
        assignment = UserHasRole(user_id=user_id, role_id=role_id)
        db.add(assignment)
        await db.commit()
        return True

    @staticmethod
    async def remove_role(db: AsyncSession, user_id: int, role_id: int) -> bool:
        """Remove role from user"""
        query = select(UserHasRole).where(
            UserHasRole.user_id == user_id,
            UserHasRole.role_id == role_id
        )
        result = await db.execute(query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            return False

        await db.delete(assignment)
        await db.commit()
        return True