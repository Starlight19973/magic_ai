"""
Настройка базы данных SQLite с SQLAlchemy.
Использует асинхронный движок для работы с Quart.
"""
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

# Путь к файлу БД
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/neuromagic.db"

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установить в True для отладки SQL-запросов
    future=True,
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
    from app.models import User, UserCourse  # noqa: F401
    from sqlalchemy.exc import OperationalError
    
    try:
        async with engine.begin() as conn:
            # Создаём только те таблицы, которых ещё нет
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    except OperationalError as e:
        # Игнорируем ошибку "table already exists" при параллельном старте воркеров
        if "already exists" not in str(e):
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

