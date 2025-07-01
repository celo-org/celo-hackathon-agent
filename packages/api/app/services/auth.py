"""
Authentication service for the API.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import Depends
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.db.models import User
from app.db.session import get_db_session
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any]) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (usually user ID)

    Returns:
        str: JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: The plaintext password
        hashed_password: The hashed password

    Returns:
        bool: True if the password matches the hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get a password hash.

    Args:
        password: The plaintext password

    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


async def authenticate_user(
    db: AsyncSession, username_or_email: str, password: str
) -> Optional[User]:
    """
    Authenticate a user by username/email and password.

    Args:
        db: Database session
        username_or_email: Username or email
        password: Password

    Returns:
        Optional[User]: The user if authentication is successful, None otherwise
    """
    # Query user by username or email
    query = select(User).where(
        or_(User.username == username_or_email, User.email == username_or_email)
    )
    result = await db.execute(query)
    user = result.scalars().first()

    # Check if user exists and password is correct
    if not user or not verify_password(password, user.password_hash):
        return None

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted login: {username_or_email}")
        return None

    return user


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user_data: User creation data

    Returns:
        User: The created user
    """
    # Create new user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
    )

    # Add to database
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get a user by username.

    Args:
        db: Database session
        username: Username

    Returns:
        Optional[User]: The user if found, None otherwise
    """
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email.

    Args:
        db: Database session
        email: Email

    Returns:
        Optional[User]: The user if found, None otherwise
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Optional[User]: The user if found, None otherwise
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalars().first()


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the auth service.

        Args:
            db: Database session
        """
        self.db = db

    async def authenticate(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Authenticate a user.

        Args:
            username_or_email: Username or email
            password: Password

        Returns:
            Optional[User]: The user if authentication is successful, None otherwise
        """
        return await authenticate_user(self.db, username_or_email, password)

    async def create_new_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            User: The created user
        """
        return await create_user(self.db, user_data)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        return await get_user_by_username(self.db, username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: Email

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        return await get_user_by_email(self.db, email)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User ID

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        return await get_user_by_id(self.db, user_id)


async def get_auth_service(db: AsyncSession = Depends(get_db_session)):
    """Get auth service instance."""
    return AuthService(db)
