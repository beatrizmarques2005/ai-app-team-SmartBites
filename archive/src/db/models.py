"""SQLAlchemy models for SmartBites

This file defines a minimal set of models used in the app. The schema is
intentionally lightweight and can be extended as needed.
"""
from datetime import datetime

# Make SQLAlchemy optional at import time so the rest of the package can be
# imported in environments where SQLAlchemy isn't installed (e.g. CI or a
# lightweight dev environment). If SQLAlchemy is present we use the real
# types; otherwise we expose minimal placeholders so import-time doesn't fail.
try:
    from sqlalchemy import (
        Column,
        Integer,
        String,
        Date,
        DateTime,
        Float,
        Text,
        Boolean,
        JSON,
        ForeignKey,
    )
    from sqlalchemy.orm import relationship
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()
    _SQLALCHEMY_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    # Lightweight placeholders so classes can be defined without SQLAlchemy.
    Column = lambda *a, **k: None
    Integer = String = Date = DateTime = Float = Text = Boolean = JSON = object
    ForeignKey = lambda *a, **k: None
    def relationship(*a, **k):
        return None

    class _DummyBase:
        pass

    Base = _DummyBase
    _SQLALCHEMY_AVAILABLE = False


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    diet_type = Column(String, nullable=True)
    allergies = Column(JSON, nullable=True)
    intolerances = Column(JSON, nullable=True)
    number_of_members = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PantryItem(Base):
    __tablename__ = "pantry_items"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    normalized_name = Column(String, index=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    open_date = Column(String, nullable=True)  # store as string DD-MM-YYYY
    shelf_life = Column(Integer, nullable=True)
    source_receipt_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    normalized_name = Column(String, index=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    section = Column(String, nullable=True)
    auto_added_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MealPlan(Base):
    __tablename__ = "meal_plans"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    slots = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MealHistory(Base):
    __tablename__ = "meal_history"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    date = Column(String, nullable=True)
    meal = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    recipe_id = Column(String, ForeignKey("recipes.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Receipt(Base):
    __tablename__ = "receipts"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    store_name = Column(String, nullable=True)
    purchase_date = Column(String, nullable=True)
    items = Column(JSON, nullable=True)
    subtotal = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    raw = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
