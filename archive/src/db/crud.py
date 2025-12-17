"""Simple CRUD helpers using SQLAlchemy session

This module provides lightweight helpers for common operations used by
services. It intentionally keeps dependencies minimal and focuses on
convenience functions (get, create, update, delete, list).

The module is tolerant to missing SQLAlchemy at import time so the rest of
the package can be imported in environments where SQLAlchemy isn't
installed. If SQLAlchemy is missing the functions remain defined but will
raise an informative error when used.
"""
from typing import Any, Dict, Optional
try:
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import NoResultFound
    _SQLALCHEMY_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Session = object
    class NoResultFound(Exception):
        pass
    _SQLALCHEMY_AVAILABLE = False


def get(session: Session, model, id: str):
    if not _SQLALCHEMY_AVAILABLE:
        raise RuntimeError("SQLAlchemy is required to use CRUD helpers. Install sqlalchemy to proceed.")
    return session.query(model).get(id)


def list_all(session: Session, model, filters: Optional[Dict[str, Any]] = None):
    if not _SQLALCHEMY_AVAILABLE:
        raise RuntimeError("SQLAlchemy is required to use CRUD helpers. Install sqlalchemy to proceed.")
    q = session.query(model)
    if filters:
        q = q.filter_by(**filters)
    return q.all()


def create(session: Session, instance):
    if not _SQLALCHEMY_AVAILABLE:
        raise RuntimeError("SQLAlchemy is required to use CRUD helpers. Install sqlalchemy to proceed.")
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance


def update(session: Session, model, id: str, changes: Dict[str, Any]):
    if not _SQLALCHEMY_AVAILABLE:
        raise RuntimeError("SQLAlchemy is required to use CRUD helpers. Install sqlalchemy to proceed.")
    obj = session.query(model).get(id)
    if not obj:
        return None
    for k, v in changes.items():
        setattr(obj, k, v)
    session.commit()
    session.refresh(obj)
    return obj


def delete(session: Session, model, id: str):
    if not _SQLALCHEMY_AVAILABLE:
        raise RuntimeError("SQLAlchemy is required to use CRUD helpers. Install sqlalchemy to proceed.")
    obj = session.query(model).get(id)
    if not obj:
        return False
    session.delete(obj)
    session.commit()
    return True
