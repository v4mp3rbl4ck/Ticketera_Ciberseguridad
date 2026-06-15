from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

connect_args = {'check_same_thread': False} if settings.DATABASE_URL.startswith('sqlite') else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
