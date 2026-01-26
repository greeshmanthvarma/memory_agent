from fastapi import APIRouter, Depends, HTTPException, Cookie
from fastapi.responses import JSONResponse
from app.db_models import UserModel
from app.models import UserRegister, UserLogin
from app.database import get_db
from app.services.auth_service import hash_password, verify_password
from app.services.qdrant_service import create_collection, delete_collection
from app.middleware.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import jwt
import os

auth_router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)

@auth_router.post("/register")
async def register(user: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(status_code=500, detail="JWT secret not found")

        new_user = None
        result = await db.execute(select(UserModel).filter((UserModel.email == user.email) | (UserModel.username == user.username)))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        try:
            create_collection(name=f"{user.username}_memories")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{str(e)}")

        new_user = UserModel(
            email=user.email,
            username=user.username,
            password=hash_password(user.password),
            collection_name=f"{user.username}_memories",
        )

        

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        
        

        jwt_token = jwt.encode({"user_id": new_user.id}, jwt_secret, algorithm="HS256")

       
        response = JSONResponse(content={"message": "Registration successful"})
        response.set_cookie(
            key="token",
            value=jwt_token,
            httponly=True,
            secure=False,
            max_age=3600,
            samesite="lax"
        )
        
        return response
    except HTTPException:
        if new_user and new_user.id:
            try:
                await db.delete(new_user)
                await db.commit()
            except:
                await db.rollback()
        try:
            delete_collection(collection_name=f"{user.username}_memories")
        except:
            pass
        raise
    except Exception as e:
        if new_user and new_user.id:
            try:
                await db.delete(new_user)
                await db.commit()
            except:
                await db.rollback()
        try:
            delete_collection(collection_name=f"{user.username}_memories")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Registration Failed: {str(e)}")

@auth_router.post("/login")
async def login(user:UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise HTTPException(status_code=500, detail="JWT secret not found")
        result = await db.execute(select(UserModel).filter((UserModel.email == user.identifier) | (UserModel.username == user.identifier)))
        
        existing_user = result.scalar_one_or_none()
        
        if not existing_user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        if not verify_password(user.password, existing_user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    
        jwt_token = jwt.encode({"user_id": existing_user.id}, jwt_secret, algorithm="HS256")

       
        response = JSONResponse(content={"message": "Login successful"})
        response.set_cookie(
            key="token",
            value=jwt_token,
            httponly=True,
            secure=False,
            max_age=3600,
            samesite="lax"
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login Failed: {str(e)}")

@auth_router.get("/me")
async def get_current_user_info(user: UserModel = Depends(get_current_user)):
    return {"email": user.email, "username": user.username, "collection_name": user.collection_name}

@auth_router.post("/logout")
async def logout():
    try:
        response = JSONResponse(content={"message": "Logout successful"})
        response.delete_cookie(key="token")
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout Failed: {str(e)}")