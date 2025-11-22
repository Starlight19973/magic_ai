"""
Модель для отслеживания попыток входа (rate limiting).
Используется для защиты от подбора паролей.
"""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class LoginAttempt(Base):
    """
    Модель для отслеживания попыток входа.
    
    Используется для rate limiting:
    - Блокировка после N неудачных попыток
    - Автоматическая разблокировка через время
    """
    __tablename__ = "login_attempts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # IP или username
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<LoginAttempt {self.identifier} ({self.attempts} attempts)>"
