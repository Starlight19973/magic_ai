from pathlib import Path

from quart import Quart
from werkzeug.datastructures import ImmutableDict

from .config import Settings
from .database import init_db
from .routes.auth import bp as auth_bp
from .routes.public import bp as public_bp

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

    # Регистрация blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    @app.context_processor
    async def inject_globals():
        return {"settings": settings}

    # Инициализация базы данных при старте приложения
    @app.before_serving
    async def startup():
        """Инициализация БД перед запуском сервера"""
        await init_db()
        print("✅ Database initialized")

    return app

