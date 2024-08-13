from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi_jwt_auth import AuthJWT
from database import get_db
import bcrypt
from models import User
from schemas import UserCreate, UserLogin, UserUpdate
from pydantic import BaseSettings
from typing import List
from fastapi.security import OAuth2PasswordBearer
import requests


router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")


# JWT 설정
class Settings(BaseSettings):
    authjwt_secret_key: str = "0nVpRh2JmUnz9X4G5k3JmZ6Vb2LqTsXe"

@AuthJWT.load_config
def get_config():
    return Settings()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/signup")
async def signup(signup_data: UserCreate, db: Session = Depends(get_db)):
    """
    # username, email, password, sex 입력받음
    """
    hashed_password = get_password_hash(signup_data.password)
    new_user = User(username=signup_data.username, email=signup_data.email, hashed_password=hashed_password, usersex=signup_data.usersex)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Signup successful", "user_id": new_user.id}

@router.post("/login")
async def login(
    request: Request,  # Request 인자를 가장 앞으로 이동
    signin_data: UserLogin,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == signin_data.username).first()

    if user and verify_password(signin_data.password, user.hashed_password):
        access_token = Authorize.create_access_token(subject=str(user.id))  # 사용자 ID를 JWT의 subject로 설정
        request.session['user_id'] = user.id  # 로그인한 사용자 ID를 세션에 저장
        return {"message": "Login successful", "access_token": access_token,"user_id":user.id}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/users", response_model=List[UserCreate])
async def read_users(request: Request, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # 세션에서 사용자 ID를 가져오기
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not logged in")

    users = db.query(User).offset(skip).limit(limit).all()
    return users



@router.get("/{user_id}", response_model=UserCreate)
async def read_user(user_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = user_update.username
    user.email = user_update.email
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# 포인트 추가 엔드포인트부분 수정금지

@router.post("/add_points/{user_id}")
async def add_points(user_id: int, points: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 포인트 추가
    user.points += points
    db.commit()
    return {"message": f"{points} points added to user {user_id}", "new_points_balance": user.points}


@router.get("/points/{user_id}")
async def get_points(user_id: int, db: Session = Depends(get_db)):
    # JWT 검증을 제거하고 바로 데이터베이스에서 유저의 포인트를 불러옴
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "points": user.points}