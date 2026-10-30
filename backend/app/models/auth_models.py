from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str

class LogoutResponse(BaseModel):
    message: str

if hasattr(TokenResponse, "model_rebuild"):
    TokenResponse.model_rebuild()
else:
    TokenResponse.update_forward_refs()
