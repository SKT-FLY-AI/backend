from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import image, bcrypt, register
import chatgpt, tmap, os, googlemap
from database import init_db, get_db
from sqlalchemy.orm import Session 
from models import User  
from passlib.context import CryptContext
from cardnews import router as cardnews_router
from poopt import router as poopt_router
from map import router as map_router
from register import router as kakao_router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
router = APIRouter()

# Secret key loaded from environment variable
session_secret_key = os.getenv("SESSION_SECRET_KEY")
jwt_secret_key = os.getenv("AUTHJWT_SECRET_KEY")

# Apply session middleware
app.add_middleware(SessionMiddleware, secret_key=session_secret_key)


class Token(BaseModel):
    access_token: str
    token_type: str

class Settings(BaseModel):
    authjwt_secret_key: str = jwt_secret_key

@AuthJWT.load_config
def get_config():
    return Settings()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://0.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 접근을 허용. 필요에 따라 특정 도메인으로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

init_db()

app.include_router(register.router, prefix="/users", tags=["users"])
app.include_router(image.router, prefix="/images", tags=["images"])
app.include_router(chatgpt.router, prefix="/chatgpt", tags=["ChatGpt"])
app.include_router(googlemap.router, prefix="/maps", tags=["maps"])
app.include_router(cardnews_router, prefix="/cardnews", tags=["cardnews"])
app.include_router(poopt_router, prefix="/chatgpt", tags=["ChatGpt"])
app.include_router(map_router, prefix="/map", tags=["maps"])
app.include_router(kakao_router, prefix="/users", tags=["users"])

@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application"}

# JWT protected endpoint
@app.get("/protected")
def protected_route(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except AuthJWTException as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    return {"message": "You are authenticated", "user_id": Authorize.get_jwt_subject()}

@app.get("/hometime")
async def hometime(start: str, end: str):
    try:
        start_poi = tmap.get_poi_by_keyword(start)
        end_poi = tmap.get_poi_by_keyword(end)
        total_time = tmap.get_total_time(start_poi, end_poi)
        return {"result": total_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
