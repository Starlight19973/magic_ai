"""
Скрипт для создания тестового пользователя.
Запуск: python create_test_user.py
"""
import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Импорты моделей
from app.models import Base, User

# Путь к БД
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/neuromagic.db"


async def create_test_user():
    """Создаёт тестового пользователя в БД"""
    
    # Создание движка и сессии
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Проверка существования пользователя
        result = await session.execute(select(User).where(User.username == "testuser"))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("⚠️  Тестовый пользователь уже существует!")
            print(f"   Username: {existing_user.username}")
            print(f"   Email: {existing_user.email}")
            return
        
        # Создание тестового пользователя
        test_user = User(
            username="testuser",
            email="test@neuromagic.ru",
            avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=testuser"
        )
        test_user.set_password("test123")  # Простой пароль для тестирования
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        print("\n✅ Тестовый пользователь успешно создан!")
        print("\n" + "="*50)
        print("📋 ДАННЫЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ:")
        print("="*50)
        print(f"   Username: testuser")
        print(f"   Email:    test@neuromagic.ru")
        print(f"   Password: test123")
        print(f"   ID:       {test_user.id}")
        print(f"   Avatar:   {test_user.avatar_url}")
        print("="*50)
        print("\n💡 Используйте эти данные для входа на сайте")
        print("   URL: http://127.0.0.1:5000/auth/login\n")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_test_user())

