"""
Настройка базы данных с SQLAlchemy.
Использует PostgreSQL с асинхронным движком для работы с Quart.
"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

# Получаем DATABASE_URL из переменной окружения (обязательно!)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required! "
        "Please set it in your .env file. "
        "Example: DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname"
    )

# Создание асинхронного движка PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установить в True для отладки SQL-запросов
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,  # Размер пула соединений
    max_overflow=20,  # Максимум дополнительных соединений
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Инициализация базы данных.
    Создаёт все таблицы, определённые в моделях.
    
    Обрабатывает ошибки конкуренции когда несколько воркеров
    одновременно пытаются создать таблицы.
    """
    # Импортируем все модели чтобы они были зарегистрированы
    from app.models import (  # noqa: F401
        User, 
        UserCourse, 
        EmailVerification, 
        LoginAttempt,
        Payment,
        CourseModule,
        Lesson,
        UserLessonProgress
    )
    from loguru import logger
    from sqlalchemy.exc import IntegrityError

    try:
        logger.info(f"Initializing database: {DATABASE_URL}")
        async with engine.begin() as conn:
            # Создаём только те таблицы, которых ещё нет
            # checkfirst=True должен предотвратить конфликты, но для надёжности
            # оборачиваем в try-except
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.success("Database initialized successfully!")
    except IntegrityError as e:
        # Игнорируем ошибки дублирования - это нормально при параллельном запуске воркеров
        if "duplicate key" in str(e).lower() or "already exists" in str(e).lower():
            logger.warning(f"Database tables already exist (race condition with other workers): {type(e).__name__}")
            logger.success("Database initialization completed (tables already created)")
        else:
            logger.error(f"Database integrity error: {type(e).__name__}: {e}")
            raise
    except Exception as e:
        logger.error(f"Database initialization failed: {type(e).__name__}: {e}")
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.
    Используется в роутах для работы с базой данных.
    
    Yields:
        AsyncSession: сессия базы данных
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

