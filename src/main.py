from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import image, bcrypt,register
import chatgpt,tmap, os, googlemap
from database import init_db, get_db
from sqlalchemy.orm import Session 
from models import User  
from passlib.context import CryptContext
from cardnews import router as cardnews_router
from poopt import router as poopt_router




app = FastAPI()
router = APIRouter()

# 똥바타 전용
# app.include_router(store_router, prefix="/store")

# 미들웨어 설정
app.add_middleware(SessionMiddleware, secret_key="0nVpRh2JmUnz9X4G5k3JmZ6Vb2LqTsXe")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str

class Settings(BaseModel):
    authjwt_secret_key: str = "0nVpRh2JmUnz9X4G5k3JmZ6Vb2LqTsXe"

@AuthJWT.load_config
def get_config():
    return Settings()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://0.0.0.1:8000",
    "http://223.194.44.32:8000",
    "http://223.194.44.32:8080"

]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="0nVpRh2JmUnz9X4G5k3JmZ6Vb2LqTsXe")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

init_db()

app.include_router(register.router, prefix="/users", tags=["users"])
app.include_router(image.router, prefix="/images", tags=["images"])
app.include_router(chatgpt.router, prefix="/chatgpt", tags=["ChatGpt"])
app.include_router(googlemap.router, prefix="/maps", tags=["maps"])  # googlemap 라우터 추가
# app.include_router(store.router, prefix="/maps", tags=["maps"]) 
app.include_router(cardnews_router, prefix="/cardnews", tags=["cardnews"])
app.include_router(poopt_router, prefix="/chatgpt", tags=["ChatGpt"])




@app.get("/")
async def read_root():
    return {"message": "Welcome to the FastAPI application"}

# JWT 보호된 엔드포인트
@app.get("/protected")
def protected_route(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required()
    except AuthJWTException as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    return {"message": "You are authenticated", "user_id": Authorize.get_jwt_subject()}



# tmap 이동경로
@app.get("/hometime")
async def hometime(start: str, end: str):
    """
    # tmap api쓴건데 구글맵이 더 편함 ㅎ.. 아직 사용 x
    """
    start_poi = tmap.get_poi_by_keyword(start)
    end_poi = tmap.get_poi_by_keyword(end)
    total_time = tmap.get_total_time(start_poi, end_poi)
    return {"result": total_time}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))