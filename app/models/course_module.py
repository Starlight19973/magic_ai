"""
Модель модуля курса (главы).
Каждый курс состоит из нескольких модулей, каждый модуль содержит несколько уроков.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class CourseModule(Base):
    """
    Модель модуля (главы) курса.

    Например: "Глава 1: Первое знакомство с магией"
    Каждый модуль содержит несколько уроков.
    """
    __tablename__ = "course_modules"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # "ai-for-beginners"

    # Порядок и отображение
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # "🔮 Глава 1: Первое знакомство"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Описание модуля

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Связи
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CourseModule #{self.id} {self.course_slug} - {self.title}>"

    def to_dict(self) -> dict:
        """Возвращает словарь с данными модуля"""
        return {
            "id": self.id,
            "course_slug": self.course_slug,
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
