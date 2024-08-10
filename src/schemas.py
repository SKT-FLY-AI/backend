from pydantic import BaseModel
from datetime import datetime
from database import Base, engine
from typing import TYPE_CHECKING, List



class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: str
    email: str

class ImageCreate(BaseModel):
    file_path: str

class ImageResponse(BaseModel):
    id: int
    user_id: int
    file_path: str
    upload_time: datetime
    file_name: str  # 파일 이름 필드 추가

    class Config:
        orm_mode = True

# 똥바타 아이템
class ItemBase(BaseModel):
    name: str
    description: str = None
    price: int

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int

    class Config:
        orm_mode = True

class UserItem(BaseModel):
    id: int
    user_id: int
    item_id: int

    class Config:
        orm_mode = True