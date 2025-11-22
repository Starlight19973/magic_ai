from pathlib import Path

from quart import Quart
from quart_auth import QuartAuth, AuthUser
from werkzeug.datastructures import ImmutableDict
from sqlalchemy import select

from .config import Settings
from .database import init_db, AsyncSessionLocal
from .routes.auth import bp as auth_bp
from .routes.public import bp as public_bp
from .routes.quest import bp as quest_bp
from .routes.courses import bp as courses_bp
from .routes.payments import payments_bp
from .models import User

# Quart 0.19.6 использует flask.sansio.App, в котором отсутствует флаг
# PROVIDE_AUTOMATIC_OPTIONS. Патчим дефолты, чтобы не получать KeyError
# при регистрации статики на Windows.
if "PROVIDE_AUTOMATIC_OPTIONS" not in Quart.default_config:
    Quart.default_config = ImmutableDict(
        {**Quart.default_config, "PROVIDE_AUTOMATIC_OPTIONS": True}
    )

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Quart:
    settings = Settings()

    app = Quart(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        template_folder=str(BASE_DIR / "templates"),
    )
    app.config.update(settings.model_dump())
    app.secret_key = settings.secret_key

    # Инициализация Quart-Auth для сессий и аутентификации
    auth_manager = QuartAuth(app)

    # Загрузчик пользователей для Quart-Auth
    @auth_manager.user_class
    class CustomAuthUser(AuthUser):
        def __init__(self, auth_id: str):
            super().__init__(auth_id)
            self._resolved = False
            self._user = None

        async def _resolve(self):
            if not self._resolved:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(User).where(User.id == int(self.auth_id))
                    )
                    self._user = result.scalar_one_or_none()
                    self._resolved = True

    # Регистрация blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(quest_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(payments_bp)

    @app.context_processor
    async def inject_globals():
        return {"settings": settings}

    # Middleware для проверки срока действия сессии
    from app.middleware.session import check_session_expiry
    
    @app.before_request
    async def before_request():
        """Проверка срока действия сессии перед каждым запросом"""
        await check_session_expiry()

    # Инициализация базы данных при старте приложения
    @app.before_serving
    async def startup():
        """Инициализация БД перед запуском сервера"""
        await init_db()

    return app

