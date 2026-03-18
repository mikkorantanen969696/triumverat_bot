#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота
"""

import asyncio
import logging
import signal
import sys
from bot import main

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BotRunner:
    """Класс для управления запуском бота"""
    
    def __init__(self):
        self.bot_task = None
        self.running = False
    
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск Telegram бота...")
            self.running = True
            await main()
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске бота: {e}")
            raise
    
    async def stop(self, signum=None, frame=None):
        """Остановка бота"""
        logger.info("🛑 Остановка бота...")
        self.running = False
        
        if self.bot_task:
            self.bot_task.cancel()
            try:
                await self.bot_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Бот остановлен")
        sys.exit(0)
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
    
    async def run(self):
        """Основной метод запуска"""
        self.setup_signal_handlers()
        
        try:
            await self.start()
        except KeyboardInterrupt:
            await self.stop()
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            await self.stop()

async def main_runner():
    """Главная функция для запуска"""
    runner = BotRunner()
    await runner.run()

if __name__ == "__main__":
    try:
        asyncio.run(main_runner())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
