import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

import urllib.parse

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Handle special characters like '@' in database passwords automatically
if "://" in db_url and db_url.count("@") > 1:
    try:
        prefix, remainder = db_url.split("://", 1)
        parts = remainder.rsplit("@", 1)
        user_pass = parts[0]
        host_part = parts[1]
        if ":" in user_pass:
            user, pwd = user_pass.split(":", 1)
            pwd_encoded = urllib.parse.quote_plus(pwd)
            db_url = f"{prefix}://{user}:{pwd_encoded}@{host_part}"
    except Exception:
        pass

if "VERCEL" in os.environ and db_url.startswith("sqlite"):
    db_url = "sqlite:////tmp/sketch2code.db"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
