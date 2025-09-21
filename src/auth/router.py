from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .service import AuthService
from .schemas import UserCreate, UserLogin, Token, User
from .dependencies import get_current_user
from ..models import User as UserModel

router = APIRouter()

@router.post("/register", response_model=User)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)

    # Check if user already exists
    existing_user = await service.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    return await service.create_user(user)

@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    service = AuthService(db)
    token = await service.login(user_login)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token

@router.get("/verify")
async def verify_token(current_user: UserModel = Depends(get_current_user)):
    user_schema = User.model_validate(current_user)
    return {"user": user_schema}