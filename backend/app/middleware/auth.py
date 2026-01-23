from fastapi import HTTPException, Cookie, Depends
from fastapi.security import HTTPBearer
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.db_models import UserModel
from sqlalchemy import select
import jwt
import os


async def get_user_from_token(token: str, db: AsyncSession):
    """
    Helper function to get user from JWT token.
    Can be used by both HTTP endpoints and WebSocket endpoints.
    """
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        user_id = payload["user_id"]
        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


async def get_current_user(token: str = Cookie(None), db: AsyncSession = Depends(get_db)):
    """
    Get current user from JWT token in cookie (for HTTP endpoints).
    """
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database dependency not injected")
        return await get_user_from_token(token, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")