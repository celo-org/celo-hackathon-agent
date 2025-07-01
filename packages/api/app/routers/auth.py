"""
Authentication router for the API.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.token import Token, TokenPayload
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.auth import (
    create_access_token,
    get_auth_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get the current user from JWT token.

    Args:
        token: JWT token
        db: Database session

    Returns:
        User: The current user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        token_data = TokenPayload(sub=user_id)
    except JWTError:
        logger.warning("JWT validation failed")
        raise credentials_exception

    # Get the auth service
    auth_service = await get_auth_service(db)

    # Get the user
    user = await auth_service.get_by_id(token_data.sub)

    if user is None:
        logger.warning(f"User not found: {token_data.sub}")
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user: {user.id}")
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        User: The created user

    Raises:
        HTTPException: If username or email already exists
    """
    # Get the auth service
    auth_service = await get_auth_service(db)

    # Check if username already exists
    existing_user = await auth_service.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email already exists
    existing_email = await auth_service.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create the user
    user = await auth_service.create_new_user(user_data)

    # Convert UUID to string for the response
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db_session),
):
    """
    Log in and get an access token.

    Args:
        form_data: OAuth2 form data with username and password
        db: Database session

    Returns:
        Token: Access token

    Raises:
        HTTPException: If authentication fails
    """
    # Get the auth service
    auth_service = await get_auth_service(db)

    # Authenticate user
    user = await auth_service.authenticate(form_data.username, form_data.password)

    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Log in with JSON data and get an access token.

    Args:
        login_data: Login data with username and password
        db: Database session

    Returns:
        Token: Access token

    Raises:
        HTTPException: If authentication fails
    """
    # Get the auth service
    auth_service = await get_auth_service(db)

    # Authenticate user
    user = await auth_service.authenticate(login_data.username, login_data.password)

    if not user:
        logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User: User information
    """
    return UserRead(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
