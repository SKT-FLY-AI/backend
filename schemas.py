from pydantic import BaseModel
from datetime import datetime
from typing import Optional



class PooptRequest(BaseModel):
    user_id: int
    message: str  # 기본값을 지정해 필드를 선택적으로 만듭니다.

class DogCreate(BaseModel):
    user_id: int
    dogname: str
    dogage: int
    dogsex: int
    dogspayed: bool
    dogpregnant: bool

class DogResponse(BaseModel):
    dogname: str
    dogage: int
    dogsex: int
    dogspayed: bool
    dogpregnant: bool

    class Config:
        orm_mode = True
class UserID(BaseModel):
    user_id : int

class UserCreate(BaseModel):
    # username: str
    email: str
    password: str                   

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    # username: str
    email: str

class UserResponse(BaseModel):
    user_id: int
    email: str 
    dog_info: DogResponse = None

    class Config:
        orm_mode = True
 

class ImageCreate(BaseModel):
    file_path: str
    user_id: int


class ImageResponse(BaseModel):
    id: int
    user_id: int
    file_path: str
    upload_time: datetime  # datetime을 문자열로 변환
    file_name: str
    poo_type: str
    poo_color: str
    # poo_blood: bool
    dogsex: int

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # datetime 객체를 ISO 형식의 문자열로 변환
        }

class ImageResponseWithoutPoints(BaseModel):
    id: int
    user_id: int
    file_path: str
    upload_time: datetime
    file_name: str
    poo_type: str
    poo_color: str
    # poo_blood: int

    class Config:
        orm_mode = True


# class ItemBase(BaseModel):
#     name: str
#     description: str = None
#     price: int

# class ItemCreate(ItemBase):
#     pass

# class Item(ItemBase):
#     id: int

#     class Config:
#         orm_mode = True

# class UserItem(BaseModel):
#     id: int
#     user_id: int
#     item_id: int

#     class Config:
#         orm_mode = True


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
    poo_type: str
    # poo_blood: int = None

    class Config:
        orm_mode = True
