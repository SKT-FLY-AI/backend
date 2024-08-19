from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 길이 50 지정
    email = Column(String(100), unique=True, index=True, nullable=False)     # 길이 100 지정
    hashed_password = Column(String(128), nullable=False)                    # 길이 128 지정
    points = Column(Integer, default=0)                                      # 포인트 필드 추가, 기본값 0
    images = relationship("Image", back_populates="user")
    items = relationship("UserItem", back_populates="user")  # UserItem 관계 추가
    usersex = Column(Integer, default=0)                                      # 쎆쓰 필드 추가, 기본값 0 : 남자/1 : 여자

    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_path = Column(String(255), nullable=False)
    upload_time = Column(DateTime, nullable=False)
    file_name = Column(String(100), nullable=False)
    poo_type = Column(Integer, nullable=False, default=0)
    poo_color = Column(String(50), nullable=False, default='#685960')  # 여기에 기본값 설정
    poo_blood = Column(Integer, nullable=False, default=0)  # TINYINT(1)로 설정
    usersex = Column(Integer)  
    doubt = Column(String(100))  




    user = relationship("User", back_populates="images")

#똥바타 아이템
class UserItem(Base):
    __tablename__ = "user_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    user = relationship("User", back_populates="items")
    item = relationship("Item")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)  # 길이 100 지정
    description = Column(String(255))  # 길이 255 지정
    price = Column(Integer)


class Analyze(Base):
    __tablename__ = "analyze"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    poo_type = Column(Integer, nullable=False, default=0)
    poo_color = Column(String(50), nullable=False) #default='#685960')  # 기본값이 설정되어있음.
    poo_blood = Column(Integer, nullable=False, default=0)  # TINYINT(1)로 설정
    analysis_time = Column(DateTime, nullable=False)  # 분석 시간 추가



class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum('user', 'assistant'), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow) 
    image_id = Column(Integer, ForeignKey('images.id'), nullable=True)  # 이미지 ID 추가
    poo_color = Column(String(50), nullable=True)  # poo_color 필드 추가
    poo_type = Column(Integer, nullable=True)  # poo_type 필드 추가
    poo_blood = Column(Integer, nullable=True)  # poo_blood 필드 추가


    user = relationship("User", back_populates="chat_logs")
    image = relationship("Image")  # 이미지를 참조하는 관계 추가
