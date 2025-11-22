"""
Модель пользователя для системы авторизации.
Использует SQLAlchemy для работы с PostgreSQL.
"""
from datetime import datetime
from typing import Optional

import bcrypt
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy"""
    pass


class User(Base):
    """
    Модель пользователя с поддержкой обычной авторизации и Telegram OAuth.
    
    Поля:
    - id: уникальный идентификатор
    - username: логин пользователя (уникальный)
    - email: email пользователя (уникальный)
    - password_hash: хеш пароля (bcrypt)
    - telegram_id: ID пользователя в Telegram (опционально)
    - telegram_username: username в Telegram (опционально)
    - avatar_url: URL аватара (по умолчанию стандартный)
    - is_active: активен ли пользователь
    - created_at: дата регистрации
    """
    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Telegram OAuth
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    telegram_username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Профиль
    avatar_url: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        default="https://api.dicebear.com/7.x/avataaars/svg?seed=default"
    )
    
    # Метаданные
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        """
        Устанавливает хеш пароля используя bcrypt.
        
        Args:
            password: пароль в открытом виде
        """
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Проверяет пароль пользователя.
        
        Args:
            password: пароль для проверки
            
        Returns:
            True если пароль верный, False иначе
        """
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self) -> str:
        return f"<User {self.username} (#{self.id})>"

    def to_dict(self) -> dict:
        """Возвращает словарь с данными пользователя (безопасный для JSON)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "telegram_username": self.telegram_username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

