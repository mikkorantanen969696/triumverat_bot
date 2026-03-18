from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Telegram Bot Settings
    BOT_TOKEN: str
    ADMIN_TELEGRAM_ID: int
    ADMIN_USERNAME: str
    
    # Database Settings
    DATABASE_URL: str
    
    # File Paths
    PHOTOS_PATH: str = "./photos"
    PDF_PATH: str = "./pdfs"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/bot.log"
    
    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Hardcoded passwords for managers and admins (as requested)
    ADMIN_PASSWORDS: dict = {
        864433722: "admin123",  # Основной админ
        # Добавьте ID второго админа сюда
    }
    
    MANAGER_PASSWORDS: dict = {
        # Менеджер 1
        # Менеджер 2
        # Менеджер 3
        # Менеджер 4
        # Менеджер 5
    }
    
    # Cities with their topic IDs
    CITIES: dict = {
        "Москва": None,  # Укажите ID подтемы
        "Санкт-Петербург": None,  # Укажите ID подтемы
        "Новосибирск": None,  # Укажите ID подтемы
        "Екатеринбург": None,  # Укажите ID подтемы
        "Нижний Новгород": None,  # Укажите ID подтемы
        "Казань": None,  # Укажите ID подтемы
        "Челябинск": None,  # Укажите ID подтемы
        "Омск": None,  # Укажите ID подтемы
        "Самара": None,  # Укажите ID подтемы
        "Ростов-на-Дону": None,  # Укажите ID подтемы
    }
    
    class Config:
        env_file = ".env"

settings = Settings()
