"""
Быстрая инициализация системы курсов с mock-контентом.
Для тестирования без долгой AI-генерации.
"""
import asyncio
from datetime import datetime
from loguru import logger

from app.database import engine, AsyncSessionLocal
from app.models import Base, User, UserCourse, CourseModule, Lesson
from app.data.catalog import COURSES
from app.data.courses import COURSES_EXTENDED
import bcrypt


async def init_quick_test():
    """Быстрая инициализация с mock-контентом"""

    logger.info("=" * 60)
    logger.info("Quick test initialization (with mock content)")
    logger.info("=" * 60)

    # 1. Пересоздаём таблицы
    logger.info("\n[1/4] Recreating database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    logger.success("Database recreated!")

    # 2. Создаём пользователя alivederchi
    logger.info("\n[2/4] Creating user alivederchi...")
    async with AsyncSessionLocal() as session:
        password = "password123"
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user = User(
            username="alivederchi",
            email="alivederchi@example.com",
            password_hash=hashed,
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.success(f"User created! Login: alivederchi / password123")

    # 3. Добавляем все курсы пользователю
    logger.info("\n[3/4] Adding all courses to user...")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        user_result = await session.execute(select(User).where(User.username == "alivederchi"))
        user = user_result.scalar_one()

        for course in COURSES:
            user_course = UserCourse(
                user_id=user.id,
                course_slug=course.slug,
                purchased_at=datetime.utcnow(),
                price_paid=course.price,
                payment_method="test",
                status="active"
            )
            session.add(user_course)

        await session.commit()
        logger.success(f"Added {len(COURSES)} courses!")

    # 4. Создаём mock-контент для курса "ai-for-beginners"
    logger.info("\n[4/4] Creating mock content for course...")
    course_slug = "ai-for-beginners"
    course_data = COURSES_EXTENDED[course_slug]

    async with AsyncSessionLocal() as session:
        # Создаём только первый модуль с 4 уроками для теста
        module_data = course_data["program"][0]

        module = CourseModule(
            course_slug=course_slug,
            order=1,
            title=module_data["title"],
            description="Первый модуль курса - знакомство с AI"
        )
        session.add(module)
        await session.flush()

        logger.info(f"Created module: {module.title}")

        # Создаём 4 урока с простым mock-контентом
        for order, lesson_title in enumerate(module_data["lessons"], start=1):
            lesson = Lesson(
                module_id=module.id,
                order=order,
                title=lesson_title,
                content_type="text",
                content_text=f"""# {lesson_title}

## 🎯 Введение

Добро пожаловать на урок "{lesson_title}"! Это тестовый урок с mock-контентом.

## 📚 Основной материал

В этом уроке мы разбираем важные концепции:
- Концепция 1: Базовые принципы
- Концепция 2: Практическое применение
- Концепция 3: Лучшие практики

## 💡 Практические советы

1. **Совет 1**: Начните с простого
2. **Совет 2**: Практикуйтесь регулярно
3. **Совет 3**: Изучайте примеры

## ✨ Резюме

Вы изучили ключевые моменты урока. Двигайтесь дальше!

---

*Это тестовый контент. Реальный контент будет сгенерирован через AI.*
""",
                quiz_questions={
                    "questions": [
                        {
                            "question": f"Тестовый вопрос для урока '{lesson_title}'?",
                            "answers": [
                                "Вариант A (правильный)",
                                "Вариант B",
                                "Вариант C",
                                "Вариант D"
                            ],
                            "correct": 0,
                            "explanation": "Это тестовый квиз с mock-контентом"
                        }
                    ]
                },
                estimated_time_minutes=15,
                is_free=(order == 1)
            )
            session.add(lesson)
            logger.info(f"Created lesson {order}: {lesson_title}")

        await session.commit()
        logger.success("Mock content created!")

    logger.success("\n" + "=" * 60)
    logger.success("Initialization completed!")
    logger.success("=" * 60)
    logger.success("\nLogin: alivederchi / password123")
    logger.success("URL: http://localhost:8000")
    logger.success("My courses: http://localhost:8000/courses/my")
    logger.success("=" * 60)


if __name__ == "__main__":
    asyncio.run(init_quick_test())
