"""
Скрипт для генерации курса "AI для повседневной работы"
"""
import asyncio
import sys
from loguru import logger

from app.services.course_generator import get_course_generator
from app.database import AsyncSessionLocal
from app.models import User, UserCourse
from sqlalchemy import select


async def generate_ai_for_beginners():
    """Генерирует курс AI для повседневной работы"""
    logger.info("Starting course generation for: ai-for-beginners")

    generator = get_course_generator()

    # Генерируем курс
    success = await generator.generate_course(
        course_slug="ai-for-beginners",
        progress_callback=lambda done, total, name: logger.info(
            f"Progress: {done}/{total} - Generating: {name}"
        )
    )

    if success:
        logger.success("Course generated successfully!")

        # Назначаем курс пользователю testuser
        logger.info("Assigning course to testuser...")
        async with AsyncSessionLocal() as session:
            # Находим пользователя
            result = await session.execute(
                select(User).where(User.username == "testuser")
            )
            user = result.scalar_one_or_none()

            if user:
                # Проверяем, не назначен ли уже курс
                existing = await session.execute(
                    select(UserCourse).where(
                        UserCourse.user_id == user.id,
                        UserCourse.course_slug == "ai-for-beginners"
                    )
                )
                if not existing.scalar_one_or_none():
                    # Создаём связь пользователь-курс
                    user_course = UserCourse(
                        user_id=user.id,
                        course_slug="ai-for-beginners",
                        is_started=False,
                        is_completed=False,
                        progress=0
                    )
                    session.add(user_course)
                    await session.commit()
                    logger.success(f"Course assigned to testuser!")
                else:
                    logger.info("Course already assigned to testuser")
            else:
                logger.warning("User testuser not found!")

        return True
    else:
        logger.error("Course generation failed!")
        return False


if __name__ == "__main__":
    asyncio.run(generate_ai_for_beginners())
