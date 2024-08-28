from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
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
    remote_bind_address=(DB_HOST, DB_PORT),
    local_bind_address=('127.0.0.1', 0)  # 0은 사용 가능한 임의의 포트를 선택
)

server.start()

# 터널링된 포트로 새로운 데이터베이스 URL 설정
# DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{server.local_bind_port}/{DB_NAME}"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{server.local_bind_port}/{DB_NAME}"

# Engine
# engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@223.194.44.32:3306/{DB_NAME}?connect_timeout=20")
engine = create_engine(DATABASE_URL)

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

# Base
Base = declarative_base()

vector_index, text_splitter = None, None

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

def add_vectorDB(data_path):
    global vector_index, text_splitter
    # Load a PDF file, using the LangChain PyPDF loader
    loader = PyPDFLoader(data_path)
    # Split the text in chunks, using LangChain Recursive Character Text Splitter
    if text_splitter is None:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
            )

    pages = loader.load_and_split(text_splitter)
    # Create a persistent, file-based vector store, using Chroma vector store.
    directory = 'index_store'
    if vector_index is None:
        vector_index = Chroma.from_documents(
                pages, # Documents
                OpenAIEmbeddings(), # Text embedding model
                persist_directory=directory # persists the vectors to the file system
            )
    else:
        _ = vector_index.add_documents(pages)
    vector_index.persist()
    
    return vector_index