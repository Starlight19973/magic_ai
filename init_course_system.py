"""
Скрипт для инициализации системы курсов.

Что делает:
1. Пересоздаёт таблицы БД (с новыми моделями)
2. Создаёт тестового пользователя alivederchi
3. Добавляет ему все курсы как купленные
4. Генерирует контент для курса "AI для повседневной работы"
"""
import asyncio
from datetime import datetime
from loguru import logger

# Импортируем модели и сервисы
from app.database import engine, init_db, AsyncSessionLocal
from app.models import Base, User, UserCourse
from app.services.course_generator import get_course_generator
from app.data.catalog import COURSES
import bcrypt


async def recreate_database():
    """Пересоздаёт все таблицы в БД"""
    logger.info("Recreating database tables...")

    # Удаляем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("All tables dropped")

    # Создаём все таблицы заново
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created")


async def create_test_user():
    """Создаёт тестового пользователя alivederchi"""
    logger.info("Creating test user: alivederchi")

    async with AsyncSessionLocal() as session:
        # Проверяем, есть ли уже такой пользователь
        from sqlalchemy import select
        existing_user = await session.execute(
            select(User).where(User.username == "alivederchi")
        )
        user = existing_user.scalar_one_or_none()

        if user:
            logger.info("User alivederchi already exists")
            return user

        # Создаём нового пользователя
        password = "password123"  # Тестовый пароль
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user = User(
            username="alivederchi",
            email="alivederchi@example.com",
            password_hash=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.info(f"User created: alivederchi (ID: {user.id})")
        logger.info(f"Login: alivederchi / password123")
        return user


async def add_all_courses_to_user(user: User):
    """Добавляет все курсы пользователю как купленные"""
    logger.info(f"Adding all courses to user: {user.username}")

    async with AsyncSessionLocal() as session:
        # Получаем пользователя из текущей сессии
        from sqlalchemy import select
        user_result = await session.execute(select(User).where(User.id == user.id))
        user = user_result.scalar_one()

        # Добавляем каждый курс
        for course in COURSES:
            # Проверяем, не куплен ли уже
            existing = await session.execute(
                select(UserCourse).where(
                    UserCourse.user_id == user.id,
                    UserCourse.course_slug == course.slug
                )
            )
            if existing.scalar_one_or_none():
                logger.info(f"Course already purchased: {course.slug}")
                continue

            # Создаём запись о покупке
            user_course = UserCourse(
                user_id=user.id,
                course_slug=course.slug,
                purchased_at=datetime.utcnow(),
                price_paid=course.price,
                payment_method="test",
                status="active"
            )
            session.add(user_course)
            logger.info(f"Added course: {course.slug} - {course.title}")

        await session.commit()
        logger.info(f"All {len(COURSES)} courses added to user {user.username}")


async def generate_ai_course():
    """Генерирует контент для курса 'AI для повседневной работы'"""
    logger.info("Generating course content: ai-for-beginners")

    course_generator = get_course_generator()

    # Callback для отслеживания прогресса
    def progress_callback(current: int, total: int, lesson_title: str):
        logger.info(f"Progress: {current}/{total} - Generating: {lesson_title}")

    # Генерируем курс
    success = await course_generator.generate_course(
        course_slug="ai-for-beginners",
        progress_callback=progress_callback
    )

    if success:
        logger.success("Course generated successfully!")
    else:
        logger.error("Failed to generate course")

    return success


async def main():
    """Основная функция инициализации"""
    logger.info("=" * 60)
    logger.info("Starting course system initialization")
    logger.info("=" * 60)

    try:
        # 1. Пересоздаём БД с новыми таблицами
        logger.info("\n[1/4] Recreating database...")
        await recreate_database()

        # 2. Создаём тестового пользователя
        logger.info("\n[2/4] Creating test user...")
        user = await create_test_user()

        # 3. Добавляем все курсы пользователю
        logger.info("\n[3/4] Adding courses to user...")
        await add_all_courses_to_user(user)

        # 4. Генерируем контент курса
        logger.info("\n[4/4] Generating course content...")
        logger.warning("This may take 5-10 minutes...")
        await generate_ai_course()

        logger.success("\n" + "=" * 60)
        logger.success("Initialization completed successfully!")
        logger.success("=" * 60)
        logger.success("\nYou can now login with:")
        logger.success("  Username: alivederchi")
        logger.success("  Password: password123")
        logger.success("\nGo to: http://localhost:8000/courses/my")
        logger.success("=" * 60)

    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Запускаем инициализацию
    asyncio.run(main())
