# Модели базы данных для приложения
from .user import User, Base
from .user_course import UserCourse
from .email_verification import EmailVerification

__all__ = ["User", "Base", "UserCourse", "EmailVerification"]

