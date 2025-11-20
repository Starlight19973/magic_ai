# Модели базы данных для приложения
from .user import User, Base
from .user_course import UserCourse
from .email_verification import EmailVerification
from .payment import Payment
from .course_module import CourseModule
from .lesson import Lesson
from .user_lesson_progress import UserLessonProgress

__all__ = [
    "User",
    "Base",
    "UserCourse",
    "EmailVerification",
    "Payment",
    "CourseModule",
    "Lesson",
    "UserLessonProgress",
]

