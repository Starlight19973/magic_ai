#!/usr/bin/env python3
"""
Скрипт для генерации контента курса через AI (OpenRouter).
Запускается 1 раз, сохраняет контент в БД.

Использование:
    python generate_course.py [course_slug]

Примеры:
    python generate_course.py ai-for-beginners
    python generate_course.py (генерирует ai-for-beginners по умолчанию)
"""
import asyncio
import os
import sys
from loguru import logger

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, AsyncSessionLocal
from app.services.course_generator import get_course_generator
from app.models import CourseModule
from sqlalchemy import select


async def generate_course(course_slug: str = "ai-for-beginners"):
    """
    Генерирует контент курса через OpenRouter API.

    Args:
        course_slug: Slug курса для генерации (например "ai-for-beginners")
    """
    logger.info("=" * 70)
    logger.info("🎓 ГЕНЕРАЦИЯ КОНТЕНТА КУРСА")
    logger.info("=" * 70)

    # Инициализируем БД
    logger.info("Initializing database connection...")
    await init_db()

    # Проверяем, есть ли уже контент
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CourseModule).where(CourseModule.course_slug == course_slug)
        )
        existing_modules = list(result.scalars().all())

        if existing_modules:
            logger.warning(f"⚠️  Course '{course_slug}' already has {len(existing_modules)} modules!")
            logger.info("Do you want to regenerate? (This will DELETE existing content)")

            # Пропускаем, если уже сгенерировано
            logger.info("Skipping generation. Delete modules manually if you want to regenerate.")
            logger.info("=" * 70)
            return False

    # Проверяем наличие API ключа
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY not found in environment!")
        logger.info("   Add it to .env file:")
        logger.info("   OPENROUTER_API_KEY=your-key-here")
        logger.info("=" * 70)
        return False

    # Генерируем курс
    logger.info(f"\n📝 Starting course generation: {course_slug}")
    logger.warning("⏳ This will take 5-10 minutes...")
    logger.info("   Make sure you have OpenRouter credits!")
    logger.info("")

    course_generator = get_course_generator()

    # Прогресс-бар
    def progress_callback(current: int, total: int, lesson_title: str):
        progress = int((current / total) * 100) if total > 0 else 0
        logger.info(f"   [{current}/{total}] ({progress}%) Generating: {lesson_title}")

    # Запускаем генерацию
    success = await course_generator.generate_course(
        course_slug=course_slug,
        progress_callback=progress_callback
    )

    if success:
        logger.success("\n" + "=" * 70)
        logger.success("✅ COURSE GENERATED SUCCESSFULLY!")
        logger.success("=" * 70)

        # Показываем статистику
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CourseModule).where(CourseModule.course_slug == course_slug)
            )
            modules = list(result.scalars().all())

            total_lessons = sum(len(m.lessons) for m in modules)

            logger.success(f"\n📊 Statistics:")
            logger.success(f"   Course slug: {course_slug}")
            logger.success(f"   Modules generated: {len(modules)}")
            logger.success(f"   Lessons generated: {total_lessons}")
            logger.success(f"   Content saved to database ✓")

        logger.success("\n" + "=" * 70)
        return True
    else:
        logger.error("\n" + "=" * 70)
        logger.error("❌ COURSE GENERATION FAILED")
        logger.error("=" * 70)
        logger.error("\nCheck the logs above for error details")
        logger.error("=" * 70)
        return False


if __name__ == "__main__":
    # Получаем course_slug из аргументов или используем по умолчанию
    course_slug = sys.argv[1] if len(sys.argv) > 1 else "ai-for-beginners"

    # Запускаем генерацию
    success = asyncio.run(generate_course(course_slug))

    # Выход с кодом ошибки если неудачно
    sys.exit(0 if success else 1)
