"""
Модель прогресса пользователя по уроку.
Отслеживает статус прохождения урока, время, оценки за квизы.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class UserLessonProgress(Base):
    """
    Модель прогресса пользователя по конкретному уроку.

    Отслеживает:
    - Статус прохождения (не начат, в процессе, завершён)
    - Время затраченное на урок
    - Результаты квизов
    - Количество попыток
    """
    __tablename__ = "user_lesson_progress"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)

    # Статус прохождения
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)
    # Возможные значения: "not_started", "in_progress", "completed"

    # Время
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Сколько времени потратил

    # Квиз (если есть)
    quiz_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Оценка 0-100
    quiz_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Количество попыток
    quiz_passed: Mapped[bool] = mapped_column(Integer, default=False, nullable=False)  # Прошёл квиз или нет

    # Последняя активность
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Связи
    user: Mapped["User"] = relationship("User", backref="lesson_progress")
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="user_progress")

    def __repr__(self) -> str:
        return f"<UserLessonProgress user={self.user_id} lesson={self.lesson_id} status={self.status}>"

    def to_dict(self) -> dict:
        """Возвращает словарь с данными прогресса"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lesson_id": self.lesson_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "time_spent_seconds": self.time_spent_seconds,
            "quiz_score": self.quiz_score,
            "quiz_attempts": self.quiz_attempts,
            "quiz_passed": self.quiz_passed,
            "last_accessed_at": self.last_accessed_at.isoformat(),
        }
