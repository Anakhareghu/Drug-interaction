from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from app.models.auth_models import LoginRequest, TokenResponse, UserResponse, LogoutResponse
from app.services.auth_service import authenticate_user, get_current_user
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """Authenticate user with username and password, returns signed JWT token."""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"], "id": user["id"]},
        expires_delta=timedelta(minutes=expires_minutes)
    )
    
    user_resp = UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user.get("role", "Researcher")
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_minutes * 60,
        user=user_resp
    )

@router.get("/me", response_model=UserResponse)
def get_current_authenticated_user(current_user: UserResponse = Depends(get_current_user)):
    """Retrieve details of currently authenticated user from bearer token."""
    return current_user

@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: UserResponse = Depends(get_current_user)):
    """Logout endpoint confirming session invalidation on client side."""
    return LogoutResponse(
        message=f"Session for user '{current_user.username}' successfully ended."
    )
