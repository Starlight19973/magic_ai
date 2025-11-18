# Модели базы данных для приложения
from .user import User, Base
from .user_course import UserCourse

__all__ = ["User", "Base", "UserCourse"]

