from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder
import pymysql

# SSH and database configuration
SSH_HOST = "223.194.44.32"
SSH_PORT = 3391
SSH_USER = "npswml"
SSH_PASSWORD = "9405654"

DB_USER = "admin"
DB_PASSWORD = "Gkswotjr123!"
DB_HOST = "127.0.0.1"
DB_PORT = 3306  # MySQL 기본 포트
DB_NAME = "maindb"

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
engine = create_engine(DATABASE_URL)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
