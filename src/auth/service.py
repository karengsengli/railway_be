from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from datetime import timedelta
from typing import Optional

from ..models import User, Role, UserHasRole
from .schemas import UserCreate, UserLogin, Token, User as UserSchema
from .dependencies import create_access_token
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not self.verify_password(password, user.password):
            return None

        return user

    async def create_user(self, user: UserCreate) -> User:
        hashed_password = self.get_password_hash(user.password)
        db_user = User(
            name=user.name,
            email=user.email,
            password=hashed_password
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        # Assign default role (customer)
        customer_role_query = select(Role).where(Role.name == "customer")
        role_result = await self.db.execute(customer_role_query)
        customer_role = role_result.scalar_one_or_none()

        if customer_role:
            user_role = UserHasRole(user_id=db_user.id, role_id=customer_role.id)
            self.db.add(user_role)
            await self.db.commit()

        return db_user

    async def login(self, user_login: UserLogin) -> Optional[Token]:
        user = await self.authenticate_user(user_login.email, user_login.password)
        if not user:
            return None

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        user_schema = UserSchema.model_validate(user)
        return Token(access_token=access_token, token_type="bearer", user=user_schema)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()