"""DB initialization utilities

Provides helpers to create an engine, session factory and to initialize the
database (create tables). This module is tolerant to a missing SQLAlchemy
installation: it will import cleanly but will raise informative errors when
database functions are used without SQLAlchemy available.
"""
import os
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from .models import Base, _SQLALCHEMY_AVAILABLE
    _HAS_SQLALCHEMY = _SQLALCHEMY_AVAILABLE
except Exception:  # pragma: no cover - optional dependency
    create_engine = None
    sessionmaker = None
    Base = None
    _HAS_SQLALCHEMY = False


def get_engine(db_url: str = None):
    db_url = db_url or os.environ.get("DATABASE_URL") or "sqlite:///smartbites.db"
    if not _HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is not installed. Install sqlalchemy to use DB helpers.")
    return create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {})


def get_session_factory(db_url: str = None):
    if not _HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is not installed. Install sqlalchemy to use DB helpers.")
    engine = get_engine(db_url)
    return sessionmaker(bind=engine)


def init_db(db_url: str = None):
    if not _HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is not installed. Install sqlalchemy to use DB helpers.")
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return engine
