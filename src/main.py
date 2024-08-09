from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import image
import register
import chatgpt  # 추가된 부분
from database import init_db


app = FastAPI()

class Location(BaseModel):
    latitude: float
    longitude: float

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    # 필요에 따라 더 추가 가능
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
app.include_router(chatgpt.router, prefix="/chatgpt")  # 추가된 부분

@app.get('/')
async def read_root():
    return {"message": "Welcome to the FastAPI application"}

