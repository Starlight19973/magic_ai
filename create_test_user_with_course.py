#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя с сгенерированным курсом.
Использует OpenRouter API для генерации контента курса через AI.

Использование:
    python create_test_user_with_course.py
"""
import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from app.database import AsyncSessionLocal, init_db
from app.models import User, UserCourse
from app.services.course_generator import get_course_generator
from sqlalchemy import select


async def create_test_user_with_course():
    """
    Создаёт тестового пользователя и генерирует для него курс.
    """
    # Инициализируем базу данных
    logger.info("Initializing database...")
    await init_db()

    # Данные тестового пользователя
    username = "test_user"
    email = "test@neuromagic.ru"
    password = "test123456"
    course_slug = "ai-for-beginners"

    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли уже такой пользователь
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"User '{username}' already exists (ID: {existing_user.id})")
                user = existing_user
            else:
                # Создаём нового пользователя
                logger.info(f"Creating new user: {username}")
                user = User(
                    username=username,
                    email=email,
                    avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                    is_active=True
                )
                user.set_password(password)

                session.add(user)
                await session.commit()
                await session.refresh(user)

                logger.success(f"✅ User created successfully!")
                logger.info(f"   Username: {username}")
                logger.info(f"   Email: {email}")
                logger.info(f"   Password: {password}")
                logger.info(f"   ID: {user.id}")

            # Проверяем, есть ли уже курс у пользователя
            result = await session.execute(
                select(UserCourse).where(
                    UserCourse.user_id == user.id,
                    UserCourse.course_slug == course_slug
                )
            )
            existing_purchase = result.scalar_one_or_none()

            if existing_purchase:
                logger.info(f"User already has access to course '{course_slug}'")
            else:
                # Добавляем курс пользователю
                logger.info(f"Adding course '{course_slug}' to user's library...")
                user_course = UserCourse(
                    user_id=user.id,
                    course_slug=course_slug,
                    price_paid=Decimal("0.00"),  # Тестовый курс бесплатно
                    payment_method="test",
                    status="paid"
                )
                session.add(user_course)
                await session.commit()

                logger.success(f"✅ Course access granted!")

        # Генерируем контент курса (модули и уроки)
        logger.info(f"Checking if course content exists...")

        async with AsyncSessionLocal() as session:
            from app.models import CourseModule

            result = await session.execute(
                select(CourseModule).where(CourseModule.course_slug == course_slug)
            )
            existing_modules = list(result.scalars().all())

            if existing_modules:
                logger.info(f"Course content already exists ({len(existing_modules)} modules)")
                logger.info("Skipping course generation")
            else:
                logger.info(f"Generating course content for '{course_slug}'...")
                logger.warning("⚠️  This will take several minutes and requires OpenRouter API key!")
                logger.info("   Make sure OPENROUTER_API_KEY is set in .env")

                # Проверяем наличие API ключа
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    logger.error("❌ OPENROUTER_API_KEY not found in environment variables!")
                    logger.info("   Course content will NOT be generated.")
                    logger.info("   User can still access the course, but it will be empty.")
                else:
                    # Генерируем курс
                    generator = get_course_generator()

                    def progress_callback(current, total, lesson_name):
                        logger.info(f"   [{current}/{total}] Generating: {lesson_name}")

                    success = await generator.generate_course(
                        course_slug=course_slug,
                        progress_callback=progress_callback
                    )

                    if success:
                        logger.success(f"✅ Course content generated successfully!")
                    else:
                        logger.error(f"❌ Failed to generate course content")
                        logger.info("   User can still access the course, but it will be empty.")

        # Выводим итоговую информацию
        print("\n" + "="*60)
        print("🎉 TEST USER CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📧 Login credentials:")
        print(f"   URL: http://localhost:8000/login")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"\n🎓 Course access:")
        print(f"   Course: {course_slug}")
        print(f"   Profile: http://localhost:8000/profile")
        print(f"   My courses: http://localhost:8000/courses/my")
        print(f"   Direct course link: http://localhost:8000/courses/my/{course_slug}")
        print("\n" + "="*60)

    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_test_user_with_course())
