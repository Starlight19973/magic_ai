"""
Модель урока курса.
Каждый урок принадлежит модулю и содержит контент (текст, видео, квизы).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Lesson(Base):
    """
    Модель урока курса.

    Например: "Что такое AI и как он устроен"
    Содержит текстовый контент, квизы, видео (опционально).
    """
    __tablename__ = "lessons"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_modules.id"), nullable=False, index=True)

    # Порядок и отображение
    order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4
    title: Mapped[str] = mapped_column(String(255), nullable=False)  # "Что такое AI"

    # Контент урока
    content_type: Mapped[str] = mapped_column(String(50), default="text", nullable=False)  # "text", "video", "quiz"
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Markdown текст урока
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # HTML версия (для быстрого отображения)

    # Видео (опционально)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # YouTube/Vimeo URL
    video_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Длительность видео

    # Изображение/обложка урока
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # URL обложки

    # Квизы (JSON формат)
    quiz_questions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Формат: {"questions": [{"question": "...", "answers": [...], "correct": 0}]}

    # Метаданные
    estimated_time_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)  # Примерное время прохождения
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Доступен без покупки (превью)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Связи
    module: Mapped["CourseModule"] = relationship("CourseModule", back_populates="lessons")
    user_progress: Mapped[list["UserLessonProgress"]] = relationship(
        "UserLessonProgress",
        back_populates="lesson",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Lesson #{self.id} {self.title}>"

    def to_dict(self) -> dict:
        """Возвращает словарь с данными урока"""
        return {
            "id": self.id,
            "module_id": self.module_id,
            "order": self.order,
            "title": self.title,
            "content_type": self.content_type,
            "content_text": self.content_text,
            "video_url": self.video_url,
            "video_duration_minutes": self.video_duration_minutes,
            "cover_image_url": self.cover_image_url,
            "quiz_questions": self.quiz_questions,
            "estimated_time_minutes": self.estimated_time_minutes,
            "is_free": self.is_free,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
