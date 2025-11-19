"""
Настройка базы данных с SQLAlchemy.
Поддерживает PostgreSQL (production) и SQLite (development).
Использует асинхронный движок для работы с Quart.
"""
import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

# Получаем DATABASE_URL из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Если не задан, используем SQLite по умолчанию (для разработки)
if not DATABASE_URL:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/neuromagic.db"

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установить в True для отладки SQL-запросов
    future=True,
    # Для PostgreSQL добавляем pool settings
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
    """
    # Импортируем все модели чтобы они были зарегистрированы
    from app.models import User, UserCourse, EmailVerification  # noqa: F401
    from loguru import logger

    try:
        logger.info(f"Initializing database: {DATABASE_URL}")
        async with engine.begin() as conn:
            # Создаём только те таблицы, которых ещё нет
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        logger.success("Database initialized successfully!")
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

