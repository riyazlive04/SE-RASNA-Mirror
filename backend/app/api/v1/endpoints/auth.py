from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_database, get_current_user
from app.schemas.user import UserSignup, UserLogin, TokenResponse, UserResponse
from app.repositories.user import UserRepository
from app.core.auth import hash_password, verify_password, create_access_token
from app.models.user import User

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserSignup,
    db: Session = Depends(get_database)
):
    """
    Create a new user account

    Requirements:
    - Email must be unique
    - Password must be at least 6 characters

    Returns:
    - JWT access token
    - User information
    """
    user_repo = UserRepository(db)

    # Check if email already exists
    if user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    # Create user
    try:
        db_user = user_repo.create({
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": password_hash,
            "domain": user_data.domain
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

    # Create access token
    access_token = create_access_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "domain": db_user.domain,
            "created_at": db_user.created_at
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_database)
):
    """
    Login with email and password

    Returns:
    - JWT access token
    - User information
    """
    user_repo = UserRepository(db)

    # Get user by email
    db_user = user_repo.get_by_email(credentials.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(data={"sub": db_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.name,
            "email": db_user.email,
            "domain": db_user.domain,
            "created_at": db_user.created_at
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information

    Requires: Valid JWT token in Authorization header
    """
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "domain": current_user.domain,
        "created_at": current_user.created_at
    }
