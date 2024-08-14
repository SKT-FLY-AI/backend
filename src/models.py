from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # 길이 50 지정
    email = Column(String(100), unique=True, index=True, nullable=False)     # 길이 100 지정
    hashed_password = Column(String(128), nullable=False)                    # 길이 128 지정
    points = Column(Integer, default=0)                                      # 포인트 필드 추가, 기본값 0
    images = relationship("Image", back_populates="user")
    items = relationship("UserItem", back_populates="user")  # UserItem 관계 추가
    sex = Column(Integer, default=0)                                      # 쎆쓰 필드 추가, 기본값 0 : 남자/1 : 여자


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
