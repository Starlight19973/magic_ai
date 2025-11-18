from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

