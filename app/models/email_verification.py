"""
Модель для хранения кодов email-верификации.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func

from . import Base


class EmailVerification(Base):
    """
    Модель для хранения кодов верификации email при регистрации.

    Поля:
    - id: уникальный идентификатор
    - email: email пользователя
    - code: 6-значный код верификации
    - created_at: время создания кода
    - expires_at: время истечения кода (10 минут)
    - is_verified: флаг использования кода
    """
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    def __init__(self, email: str, code: str):
        """
        Создает новую запись верификации.
        Автоматически устанавливает expires_at на +10 минут.
        """
        self.email = email
        self.code = code
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)

    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия кода"""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<EmailVerification {self.email} code={self.code}>"
