from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sshtunnel import SSHTunnelForwarder
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT"))
SSH_USER = os.getenv("SSH_USER")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")

# SSH 터널링 설정
server = SSHTunnelForwarder(
    (SSH_HOST, SSH_PORT),
    ssh_username=SSH_USER,
    ssh_password=SSH_PASSWORD,
    remote_bind_address=(DB_HOST, DB_PORT)
)

server.start()

# 터널링된 포트로 새로운 데이터베이스 URL 설정
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@223.194.44.32:{server.local_bind_port}/{DB_NAME}"

# Engine
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@223.194.44.32:3306/{DB_NAME}?connect_timeout=20")

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    from models import User, Image
    Base.metadata.create_all(bind=engine)
