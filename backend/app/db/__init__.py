"""Слой доступа к PostgreSQL: Base, session, ORM-модели."""

from backend.app.db.base import Base
from backend.app.db.session import get_engine, get_session_factory, session_scope

# Регистрация таблиц при импорте пакета
from backend.app.db import models as models  # noqa: F401

__all__ = ["Base", "get_engine", "get_session_factory", "session_scope", "models"]
