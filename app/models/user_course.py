"""
Модель для связи пользователей с приобретёнными курсами
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from . import Base


class UserCourse(Base):
    """Модель приобретённого курса пользователем"""
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_slug = Column(String(100), nullable=False, index=True)  # slug курса из каталога
    
    # Информация о покупке
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)  # цена в рублях
    payment_method = Column(String(50), default="mock")  # mock, etc
    
    # Статус доступа
    status = Column(
        String(20), 
        default="paid",  # paid, active, completed
        nullable=False
    )
    
    # Связь с пользователем
    user = relationship("User", backref="purchased_courses")

    def __repr__(self):
        return f"<UserCourse user_id={self.user_id} course={self.course_slug}>"

