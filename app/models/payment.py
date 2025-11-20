"""
Модель платежа для интеграции с ЮKassa.
Хранит информацию о покупках курсов пользователями.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Payment(Base):
    """
    Модель платежа для покупки курсов через ЮKassa.

    Поля:
    - id: уникальный идентификатор платежа
    - user_id: ID пользователя, который совершает покупку
    - course_id: ID курса, который покупают
    - yookassa_payment_id: ID платежа в системе ЮKassa
    - amount: сумма платежа в рублях
    - currency: валюта платежа (по умолчанию RUB)
    - status: статус платежа (pending, succeeded, canceled)
    - description: описание платежа
    - confirmation_url: URL для перехода к форме оплаты
    - created_at: дата создания платежа
    - updated_at: дата последнего обновления
    - paid_at: дата успешной оплаты
    """
    __tablename__ = "payments"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # ЮKassa данные
    yookassa_payment_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)  # сумма в рублях
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)  # валюта

    # Статус платежа
    # Возможные значения: pending, waiting_for_capture, succeeded, canceled
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)

    # Дополнительная информация
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmation_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Связи
    user: Mapped["User"] = relationship("User", backref="payments")

    def __repr__(self) -> str:
        return f"<Payment #{self.id} user={self.user_id} course={self.course_id} status={self.status}>"

    def to_dict(self) -> dict:
        """Возвращает словарь с данными платежа (безопасный для JSON)"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "yookassa_payment_id": self.yookassa_payment_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "confirmation_url": self.confirmation_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }
