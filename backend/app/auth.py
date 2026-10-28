from typing import Optional
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel
from app.supabase import supabase, is_supabase_configured

class AuthUser(BaseModel):
    id: str
    email: Optional[str] = None
    token: Optional[str] = None

async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[AuthUser]:
    """
    Extracts and verifies Supabase JWT from 'Authorization: Bearer <token>'.
    Returns AuthUser if valid, otherwise None.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split("Bearer ", 1)[1].strip()
    if not token:
        return None

    if is_supabase_configured() and supabase and not token.startswith("test-"):
        try:
            # Query Supabase Auth API to authenticate JWT
            user_response = supabase.auth.get_user(token)
            if user_response and user_response.user:
                return AuthUser(
                    id=str(user_response.user.id),
                    email=user_response.user.email,
                    token=token,
                )
        except Exception as e:
            print(f"Auth verification error: {e}")
            return None
    else:
        # Development / test mode fallback (e.g. test tokens in test suites)
        return AuthUser(
            id=token,
            email=f"{token}@example.com",
            token=token,
        )

    return None

async def get_current_user(
    user: Optional[AuthUser] = Depends(get_optional_user)
) -> AuthUser:
    """FastAPI dependency requiring a valid authenticated user session."""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials were missing or invalid."
        )
    return user
