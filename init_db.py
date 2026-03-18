#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import asyncio
import logging
from database_manager import db

async def main():
    """Основная функция инициализации"""
    try:
        print("🔄 Инициализация базы данных...")
        
        # Инициализация базы данных
        await db.init_db()
        
        print("✅ База данных успешно инициализирована!")
        print("📊 Созданы таблицы:")
        print("   - users (пользователи)")
        print("   - cleaning_requests (заявки)")
        print("   - request_photos (фото заявок)")
        print("   - payments (платежи)")
        print("   - cities (города)")
        
        print("\n🎉 Система готова к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        logging.error(f"Database initialization error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск инициализации
    asyncio.run(main())
