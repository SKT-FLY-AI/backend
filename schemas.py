from pydantic import BaseModel
from datetime import datetime
from database import Base, engine
from typing import TYPE_CHECKING, List



class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    usersex : int

class UserLogin(BaseModel):
    email: str
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
    file_name: str 
    poo_type: int  
    poo_color: str 
    poo_blood: int 
    usersex: int  
    doubt: str

    class Config:
        orm_mode = True

# 조회전용
class ImageResponseWithoutPoints(BaseModel):
    id: int
    user_id: int
    file_path: str
    upload_time: datetime
    file_name: str
    poo_type: int
    poo_color: str
    poo_blood: int
    usersex: int  # usersex 필드 추가

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


# Chat log
class ChatRequest(BaseModel):
    poo_type: str
    poo_color: str
    poo_blood: str


class ChatLogResponse(BaseModel):
    id: int
    user_id: int
    role: str
    message: str
    timestamp: datetime
    image_id: int = None
    poo_color: str = None
    poo_type: int = None
    poo_blood: int = None

    class Config:
        orm_mode = True
