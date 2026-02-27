import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# مهم: نخلي db داخل storage باش ما يطيحش
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "storage")
DB_DIR = os.path.abspath(DB_DIR)
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "learnlanguage.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()