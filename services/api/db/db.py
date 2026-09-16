from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

load_dotenv()
DATABASE_USER = os.getenv('DATABASE_USER')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')

SQLALCHEMY_DATABASE_URL = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
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