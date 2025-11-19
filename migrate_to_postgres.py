"""
Скрипт миграции данных из SQLite в PostgreSQL.

Использование:
1. Убедитесь что PostgreSQL запущен (docker-compose up -d postgres)
2. Установите переменные окружения для PostgreSQL в .env
3. Запустите: python migrate_to_postgres.py

Скрипт:
- Читает все данные из SQLite БД
- Создаёт таблицы в PostgreSQL
- Копирует все записи из SQLite в PostgreSQL
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
from loguru import logger

# Загружаем переменные окружения
load_dotenv()

# Импортируем модели
from app.models import Base, User, UserCourse, EmailVerification


async def migrate_data():
    """
    Миграция данных из SQLite в PostgreSQL.
    """
    # SQLite источник
    BASE_DIR = Path(__file__).resolve().parent
    sqlite_url = f"sqlite+aiosqlite:///{BASE_DIR}/neuromagic.db"

    # PostgreSQL назначение (из .env)
    postgres_url = os.getenv("DATABASE_URL")

    if not postgres_url:
        logger.error("DATABASE_URL не задан в .env!")
        logger.info("Пример: DATABASE_URL=postgresql+asyncpg://neuromagic_user:password@localhost:5432/neuromagic")
        return

    logger.info(f"Источник (SQLite): {sqlite_url}")
    logger.info(f"Назначение (PostgreSQL): {postgres_url}")

    # Создаём движки
    sqlite_engine = create_async_engine(sqlite_url, echo=False)
    postgres_engine = create_async_engine(postgres_url, echo=False)

    # Создаём сессии
    SQLiteSession = async_sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    PostgresSession = async_sessionmaker(postgres_engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Создаём таблицы в PostgreSQL
        logger.info("Создание таблиц в PostgreSQL...")
        async with postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Таблицы созданы!")

        # Миграция пользователей
        logger.info("Миграция пользователей...")
        async with SQLiteSession() as sqlite_session:
            async with PostgresSession() as postgres_session:
                # Читаем всех пользователей из SQLite
                result = await sqlite_session.execute(select(User))
                users = result.scalars().all()

                logger.info(f"Найдено пользователей: {len(users)}")

                for user in users:
                    # Создаём нового пользователя в PostgreSQL
                    new_user = User(
                        id=user.id,
                        username=user.username,
                        email=user.email,
                        hashed_password=user.hashed_password,
                        avatar_url=user.avatar_url,
                        is_active=user.is_active,
                        telegram_id=user.telegram_id,
                        telegram_username=user.telegram_username,
                        created_at=user.created_at,
                    )
                    postgres_session.add(new_user)
                    logger.debug(f"Копирую пользователя: {user.username}")

                await postgres_session.commit()
                logger.success(f"Мигрировано пользователей: {len(users)}")

        # Миграция курсов пользователей
        logger.info("Миграция прогресса по курсам...")
        async with SQLiteSession() as sqlite_session:
            async with PostgresSession() as postgres_session:
                result = await sqlite_session.execute(select(UserCourse))
                user_courses = result.scalars().all()

                logger.info(f"Найдено записей о курсах: {len(user_courses)}")

                for uc in user_courses:
                    new_uc = UserCourse(
                        id=uc.id,
                        user_id=uc.user_id,
                        course_id=uc.course_id,
                        is_started=uc.is_started,
                        is_completed=uc.is_completed,
                        progress=uc.progress,
                        started_at=uc.started_at,
                        completed_at=uc.completed_at,
                    )
                    postgres_session.add(new_uc)

                await postgres_session.commit()
                logger.success(f"Мигрировано записей о курсах: {len(user_courses)}")

        # Миграция email верификаций
        logger.info("Миграция email верификаций...")
        async with SQLiteSession() as sqlite_session:
            async with PostgresSession() as postgres_session:
                result = await sqlite_session.execute(select(EmailVerification))
                verifications = result.scalars().all()

                logger.info(f"Найдено верификаций: {len(verifications)}")

                for ver in verifications:
                    new_ver = EmailVerification(
                        id=ver.id,
                        email=ver.email,
                        code=ver.code,
                        is_verified=ver.is_verified,
                    )
                    new_ver.created_at = ver.created_at
                    new_ver.expires_at = ver.expires_at
                    postgres_session.add(new_ver)

                await postgres_session.commit()
                logger.success(f"Мигрировано верификаций: {len(verifications)}")

        logger.success("✅ Миграция завершена успешно!")
        logger.info("Теперь можно обновить .env и использовать PostgreSQL")

    except Exception as e:
        logger.error(f"Ошибка миграции: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await sqlite_engine.dispose()
        await postgres_engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_data())
