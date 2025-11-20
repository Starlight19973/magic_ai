#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя с доступом к курсу.
Создаёт пользователя так, как будто он оплатил курс.

Использование:
    python create_test_user.py [course_slug]

Примеры:
    python create_test_user.py ai-for-beginners
    python create_test_user.py (добавляет ai-for-beginners по умолчанию)
"""
import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from sqlalchemy import select

from app.database import init_db, AsyncSessionLocal
from app.models import User, UserCourse
from app.data.catalog import COURSES


async def create_test_user(course_slug: str = "ai-for-beginners"):
    """
    Создаёт тестового пользователя с доступом к курсу.

    Args:
        course_slug: Slug курса, к которому дать доступ
    """
    logger.info("=" * 70)
    logger.info("👤 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ")
    logger.info("=" * 70)

    # Инициализируем БД
    logger.info("Initializing database connection...")
    await init_db()

    # Данные тестового пользователя
    username = "testuser"
    email = "test@neuromagic.ru"
    password = "test123"

    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли пользователь
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.info(f"✓ User '{username}' already exists (ID: {existing_user.id})")
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
                logger.success(f"✅ User created: {username} (ID: {user.id})")

            # Проверяем курс в каталоге
            course = next((c for c in COURSES if c.slug == course_slug), None)
            if not course:
                logger.error(f"❌ Course not found in catalog: {course_slug}")
                logger.info(f"   Available courses: {', '.join(c.slug for c in COURSES)}")
                return False

            # Проверяем, есть ли уже доступ к курсу
            result = await session.execute(
                select(UserCourse).where(
                    UserCourse.user_id == user.id,
                    UserCourse.course_slug == course_slug
                )
            )
            existing_purchase = result.scalar_one_or_none()

            if existing_purchase:
                logger.info(f"✓ User already has access to course '{course_slug}'")
            else:
                # Добавляем курс пользователю (как будто оплатил)
                logger.info(f"Adding course access: {course.title}")
                user_course = UserCourse(
                    user_id=user.id,
                    course_slug=course_slug,
                    purchased_at=datetime.utcnow(),
                    price_paid=course.price,  # Цена из каталога
                    payment_method="test",  # Тестовая оплата
                    status="paid"  # Оплачен
                )
                session.add(user_course)
                await session.commit()
                logger.success(f"✅ Course access granted: {course.title}")

        # Выводим итоговую информацию
        logger.success("\n" + "=" * 70)
        logger.success("✅ TEST USER CREATED SUCCESSFULLY!")
        logger.success("=" * 70)
        logger.success(f"\n📧 Login credentials:")
        logger.success(f"   URL:      http://localhost:8000/login")
        logger.success(f"   Username: {username}")
        logger.success(f"   Password: {password}")
        logger.success(f"   Email:    {email}")

        logger.success(f"\n🎓 Course access:")
        logger.success(f"   Course: {course.title}")
        logger.success(f"   Slug:   {course_slug}")
        logger.success(f"   Price:  {course.price} ₽ (paid)")

        logger.success(f"\n🔗 Quick links:")
        logger.success(f"   Profile:      http://localhost:8000/profile")
        logger.success(f"   My courses:   http://localhost:8000/courses/my")
        logger.success(f"   Start course: http://localhost:8000/courses/my/{course_slug}")

        logger.success("\n" + "=" * 70)
        return True

    except Exception as e:
        logger.error(f"❌ Error creating test user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Получаем course_slug из аргументов или используем по умолчанию
    course_slug = sys.argv[1] if len(sys.argv) > 1 else "ai-for-beginners"

    # Запускаем создание пользователя
    success = asyncio.run(create_test_user(course_slug))

    # Выход с кодом ошибки если неудачно
    sys.exit(0 if success else 1)
