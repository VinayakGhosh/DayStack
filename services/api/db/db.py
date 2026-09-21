from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

from db.config import resolve_database_url

load_dotenv()
SQLALCHEMY_DATABASE_URL = resolve_database_url(os.environ)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=30,  # Number of connections in the pool
    max_overflow=10,  # Reduced from 30 to prevent excessive connections
    pool_timeout=30,
    pool_recycle=300,  # Recycle connections after 5 minutes
    pool_pre_ping=True,  # Test connections before using them
    echo_pool=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()   
    try:
        yield db
    finally:
        db.close()
