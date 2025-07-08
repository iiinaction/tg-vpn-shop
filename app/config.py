import os
from typing import List
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from pathlib import Path

#Путь к .env
dotenv_path = Path(__file__).parent / ".env"

# Загружаем переменные окружения
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    PROVIDER_TOKEN: str
    API_URL: str
    CERT_SHA: str
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_URL: str = 'sqlite+aiosqlite:///data/db.sqlite3'
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_FSM: int = 0
    REDIS_DB_SCHEDDULER: int = 2
    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_file_encoding = "utf-8"
    )

#Параметры для загрузки переменных среды
settings = Settings()
database_url = settings.DB_URL



#Настройки логгера
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log.txt")
logger.add(log_file_path, format=settings.FORMAT_LOG, level="INFO", rotation=settings.LOG_ROTATION)