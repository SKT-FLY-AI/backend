from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response, Query, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi_jwt_auth import AuthJWT
from database import get_db
import bcrypt
from models import User, Image, DogInfo
from schemas import UserCreate, UserLogin, UserUpdate, UserResponse, DogCreate, DogResponse, ImageResponse
from pydantic import BaseSettings
from typing import List, Any
from fastapi.security import OAuth2PasswordBearer
import requests
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse  # JSONResponse도 사용 가능
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import schemas, models

def datetime_to_str(dt):
    if dt:
        return dt.isoformat()
    return None




# Load environment variables from .env file
load_dotenv()

# FastAPI 애플리케이션 생성
app = FastAPI()
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 접근을 허용. 필요에 따라 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("0nVpRh2JmUnz9X4G5k3JmZ6Vb2LqTsXe"))


# 카카오 OAuth 환경 변수 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")

# OAuth 설정
oauth = OAuth()

oauth.register(
    name='kakao',
    client_id=KAKAO_CLIENT_ID,
    client_secret=KAKAO_CLIENT_SECRET,
    authorize_url="https://kauth.kakao.com/oauth/authorize",
    authorize_params=None,
    access_token_url="https://kauth.kakao.com/oauth/token",
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri="http://localhost:8000/users/auth/kakao/callback",  # Redirect URL 설정
    client_kwargs={'scope': 'profile_nickname, account_email'}
)






# Google OAuth 환경 변수 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# OAuth 설정
oauth = OAuth()

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={'scope': 'openid email profile'}
)


# 카카오 로그인 엔드포인트 추가
@router.get("/login/kakao")
async def kakao_login(request: Request):
    redirect_uri = request.url_for('kakao_callback')
    return await oauth.kakao.authorize_redirect(request, redirect_uri)

# 카카오 로그인 콜백 엔드포인트 추가
@router.get("/auth/kakao/callback")
async def kakao_callback(request: Request, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    token = await oauth.kakao.authorize_access_token(request)
    user_info = await oauth.kakao.parse_id_token(request, token)

    kakao_account = user_info.get("kakao_account")
    profile = kakao_account.get("profile")

    # 이메일로 사용자 검색
    user = db.query(User).filter(User.email == kakao_account.get("email")).first()

    # 새로운 사용자면 회원가입 처리
    if not user:
        user = User(
            username=profile.get("nickname"),
            email=kakao_account.get("email"),
            hashed_password="",  # 소셜 로그인 사용자는 비밀번호가 필요하지 않습니다.
            usersex=0  # 기본값으로 설정하거나 사용자에게 선택받도록 구현할 수 있습니다.
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # JWT 토큰 생성 및 반환
    access_token = Authorize.create_access_token(subject=str(user.id))
    request.session['user_id'] = user.id  # 로그인한 사용자 ID를 세션에 저장
    
    # 사용자가 업로드한 모든 이미지를 조회
    images = db.query(Image).filter(Image.user_id == user.id).all()

    return {
        "message": "Login successful via Kakao",
        "access_token": access_token,
        "user_id": user.id,
        "images": images  # 이미지 데이터 추가
    }


# 기존 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# JWT 시크릿 키 및 알고리즘 설정
SECRET_KEY = "111"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# dog전용
# 강아지 정보 등록 API
@router.post("/dog_signup", response_model=DogResponse)
async def dog_signup(
    dog_data: DogCreate, 
    db: Session = Depends(get_db)
):
    try:
        # 요청 데이터에서 user_id 가져오기
        user_id = dog_data.user_id
        print(f"User ID from request: {user_id}")
        
        if not user_id:
            print("Error: User ID not provided.")
            raise HTTPException(status_code=400, detail="User ID not provided")

        # 데이터베이스에서 사용자 조회
        user = db.query(User).filter(User.id == user_id).first()
        print(f"User retrieved from DB: {user}")
        
        if not user:
            print(f"Error: User with ID {user_id} not found in the database.")
            raise HTTPException(status_code=404, detail="User not found")

        # 새로운 강아지 정보 생성
        new_dog = DogInfo(
            user_id=user.id,
            dogname=dog_data.dogname,
            dogsex=dog_data.dogsex,
            dogage=dog_data.dogage,
            dogspayed=dog_data.dogspayed,
            dogpregnant=dog_data.dogpregnant
        )
        print(f"New dog info: {new_dog}")

        # 데이터베이스에 강아지 정보 추가
        db.add(new_dog)
        db.commit()
        db.refresh(new_dog)
        print(f"Dog registered successfully with ID: {new_dog.id}")

        # 응답 반환
        return DogResponse(
            dogname=new_dog.dogname,
            dogage=new_dog.dogage,
            dogsex=new_dog.dogsex,
            dogspayed=new_dog.dogspayed,
            dogpregnant=new_dog.dogpregnant
        )

    except Exception as e:
        # 예외 발생 시 오류 메시지 출력
        print(f"Error during dog signup: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



# 강아지 정보 조회 API
@router.get("/dog_info", response_model=List[DogResponse])
async def read_dog(user_id: int = Query(...), db: Session = Depends(get_db)):
    # `user_id`를 쿼리 파라미터로 받습니다.
    dogs = db.query(DogInfo).filter(DogInfo.user_id == user_id).all()
    
    if not dogs:
        raise HTTPException(status_code=404, detail="No dogs found for this user")

    return dogs

@router.post("/login")
async def login(signin_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == signin_data.email).first()

    if user and verify_password(signin_data.password, user.hashed_password):
        # 이미지 데이터 가져오기
        image = db.query(Image).filter(Image.user_id == user.id).first()

        if image:
            image_data = {
                "id": image.id,
                "user_id": image.user_id,
                "file_path": image.file_path,
                "upload_time": datetime_to_str(image.upload_time),  # datetime을 문자열로 변환
                "file_name": image.file_name,
                "poo_type": image.poo_type,
                "poo_color": image.poo_color,
                "poo_blood": image.poo_blood,
            }
        else:
            image_data = None

        return JSONResponse(content={"user_id": user.id, "image": image_data}, status_code=200)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/signup", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 동일한 이메일이 이미 존재하는지 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 새 사용자 생성
    new_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        email=new_user.email,
        dog_info=None  # 초기에는 개 정보가 없으므로 None
    )





app.include_router(router)


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)  # 명시적으로 Pydantic 모델로 변환하여 반환



# 사용자 정보 수정 엔드포인트 (JWT 없이 user_id로 조회)
@router.put("/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    # user_id로 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 사용자 정보 업데이트
    user.username = user_update.username
    user.email = user_update.email
    user.dogname = user_update.dogname
    user.dogage = user_update.dogage
    user.dogsex = user_update.dogsex
    db.commit()
    db.refresh(user)
    return user

# 사용자 삭제 엔드포인트 (JWT 없이 user_id로 조회)
@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    # user_id로 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # 사용자 삭제
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# 라우터를 애플리케이션에 포함
app.include_router(router)

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
