from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi_jwt_auth import AuthJWT
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import image
import register
import chatgpt
from database import init_db
from typing import Annotated
from store import router as store_router # 똥바타 전용



app = FastAPI()


#똥바타전용
app.include_router(store_router, prefix="/store")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Location(BaseModel):
    latitude: float
    longitude: float

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

init_db()

app.include_router(register.router, prefix="/users")
app.include_router(image.router, prefix="/images")
app.include_router(chatgpt.router, prefix="/chatgpt")

@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


@app.get('/')
async def read_root():
    return {"message": "Welcome to the FastAPI application"}

# JWT 설정
@app.get('/protected')
async def protected(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return {"user_id": Authorize.get_jwt_subject()}
