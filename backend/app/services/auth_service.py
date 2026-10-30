from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.security import verify_password, hash_password, create_access_token, decode_access_token
from app.models.auth_models import UserResponse

security = HTTPBearer(auto_error=False)

# Seed in-memory / configured users table with pre-hashed passwords
# Never store plaintext passwords!
_DEFAULT_HASHED_PW = hash_password(settings.DEFAULT_AUTH_PASSWORD)

USERS_DB = {
    settings.DEFAULT_AUTH_USERNAME: {
        "id": "usr-lead-01",
        "username": settings.DEFAULT_AUTH_USERNAME,
        "hashed_password": _DEFAULT_HASHED_PW,
        "email": settings.DEFAULT_AUTH_EMAIL,
        "role": settings.DEFAULT_AUTH_ROLE,
        "is_active": True
    },
    "researcher": {
        "id": "usr-res-02",
        "username": "researcher",
        "hashed_password": hash_password("pk_target_2026!"),
        "email": "clinical.fellow@lab.internal",
        "role": "Clinical Researcher",
        "is_active": True
    }
}

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate username and password against securely stored bcrypt hashes."""
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    if not user.get("is_active", True):
        return None
    return user

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """Dependency that extracts, verifies the JWT token, and returns user information."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = USERS_DB.get(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        role=user.get("role", "Researcher")
    )
