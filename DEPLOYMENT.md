# 🚀 ИНСТРУКЦИЯ ДЛЯ ДЕПЛОЯ НА TIMEWEB

## 📋 Подготовка к деплою

### 🔧 Требования
- Python 3.11+
- PostgreSQL база данных
- Токен Telegram бота
- Домен (опционально)

### 📁 Структура проекта
```
triumverat_bot/
├── bot.py                 # Основной файл бота
├── database.py           # Модели базы данных
├── database_manager.py   # Управление БД
├── config.py            # Конфигурация
├── keyboards.py         # Клавиатуры
├── utils.py             # Утилиты
├── admin_handlers.py    # Обработчики админа
├── manager_handlers.py  # Обработчики менеджера
├── cleaner_handlers.py  # Обработчики клинера
├── requirements.txt     # Зависимости
├── .env.example        # Пример конфигурации
├── DEPLOYMENT.md       # Эта инструкция
└── INSTRUCTIONS/       # Инструкции для пользователей
```

## 🌐 Настройка TimeWeb

### 1. Создание проекта
1. Войдите в панель управления TimeWeb
2. Создайте новый проект "Python"
3. Выберите Python 3.11
4. Укажите домен или используйте стандартный

### 2. Настройка базы данных PostgreSQL
1. В панели управления создайте базу данных
2. Выберите PostgreSQL
3. Запишите параметры подключения:
   - Хост (host)
   - Порт (port) 
   - Имя БД (database)
   - Пользователь (user)
   - Пароль (password)

### 3. Загрузка файлов проекта
1. Через SFTP или Git загрузите файлы проекта
2. Убедитесь, что все файлы на месте
3. Проверьте права доступа к файлам

## ⚙️ Настройка окружения

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Создание .env файла
Создайте файл `.env` в корне проекта:
```env
# Telegram Bot Settings
BOT_TOKEN=ВАШ_ТОКЕН_БОТА
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database_name
ADMIN_TELEGRAM_ID=ВАШ_TELEGRAM_ID
ADMIN_USERNAME=admin

# File Paths
PHOTOS_PATH=./photos
PDF_PATH=./pdfs

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/bot.log

# Environment
DEBUG=False
ENVIRONMENT=production
```

### 3. Настройка config.py
В файле `config.py` добавьте:
- ID подтем для городов в `CITIES`
- Пароли администраторов в `ADMIN_PASSWORDS`
- Пароли менеджеров в `MANAGER_PASSWORDS`

Пример:
```python
CITIES: dict = {
    "Москва": 12345,  # ID подтемы в ТГ группе
    "Санкт-Петербург": 12346,
    # ... другие города
}

ADMIN_PASSWORDS: dict = {
    864433722: "admin123",  # ID: пароль
    # ... другие админы
}

MANAGER_PASSWORDS: dict = {
    123456789: "manager123",  # ID: пароль
    # ... другие менеджеры
}
```

## 🗄️ Настройка базы данных

### 1. Инициализация БД
Создайте скрипт `init_db.py`:
```python
import asyncio
from database_manager import db

async def init_database():
    await db.init_db()
    print("База данных успешно инициализирована!")

if __name__ == "__main__":
    asyncio.run(init_database())
```

### 2. Запуск инициализации
```bash
python init_db.py
```

## 🚀 Запуск бота

### 1. Создание startup скрипта
Создайте файл `run_bot.py`:
```python
import asyncio
import logging
from bot import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

### 2. Настройка автозапуска
В панели TimeWeb:
1. Перейдите в "Задачи Cron"
2. Создайте задачу для автозапуска:
   ```
   @reboot cd /path/to/project && python run_bot.py
   ```
3. Добавьте задачу для перезапуска при падении:
   ```
   */5 * * * * cd /path/to/project && pgrep -f "python run_bot.py" || python run_bot.py
   ```

### 3. Настройка Gunicorn (рекомендуется)
Создайте файл `gunicorn_config.py`:
```python
bind = "0.0.0.0:8000"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

## 🔧 Мониторинг и логирование

### 1. Настройка логов
Логи автоматически пишутся в `logs/bot.log`

### 2. Мониторинг процесса
Создайте скрипт `monitor.py`:
```python
import psutil
import time
import logging

def monitor_bot():
    while True:
        # Проверяем, запущен ли бот
        bot_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'] and 'run_bot.py' in ' '.join(proc.info['cmdline'] or []):
                    bot_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if not bot_running:
            logging.error("Бот не запущен! Перезапуск...")
            import subprocess
            subprocess.run(['python', 'run_bot.py'])
        
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == "__main__":
    monitor_bot()
```

## 🔒 Безопасность

### 1. Защита .env файла
```bash
chmod 600 .env
```

### 2. Настройка Firewall
В панели TimeWeb настройте правила firewall:
- Открыть порт для SSH (22)
- Открыть порт для HTTP (80)
- Открыть порт для HTTPS (443)

### 3. SSL сертификат
1. В панели TimeWeb включите бесплатный SSL
2. Настройте автоматическое продление

## 📊 Проверка работоспособности

### 1. Тестовый запуск
```bash
python run_bot.py
```

### 2. Проверка логов
```bash
tail -f logs/bot.log
```

### 3. Проверка бота
1. Найдите бота в Telegram
2. Отправьте команду `/start`
3. Проверьте авторизацию

## 🔄 Обновление системы

### 1. Создание бэкапа
```bash
pg_dump -h host -U user database_name > backup.sql
```

### 2. Обновление кода
1. Загрузите новые файлы
2. Установите новые зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Перезапустите бота:
   ```bash
   pkill -f "python run_bot.py"
   python run_bot.py
   ```

## 🚨 Возможные проблемы

### 1. Бот не запускается
- Проверьте токен в .env
- Проверьте подключение к БД
- Посмотрите логи

### 2. Ошибка подключения к БД
- Проверьте параметры DATABASE_URL
- Убедитесь, что БД создана
- Проверьте права пользователя

### 3. Проблемы с зависимостями
- Обновите pip: `pip install --upgrade pip`
- Переустановите зависимости: `pip install -r requirements.txt --force-reinstall`

## 📞 Поддержка

### Техническая поддержка TimeWeb
- Чат поддержки в панели
- Email: support@timeweb.com
- Телефон: 8 800 775-29-12

### Разработчик системы
- GitHub Issues для баг-репортов
- Документация в папке INSTRUCTIONS/

---

**⚠️ Важно:** Регулярно делайте бэкапы базы данных и следите за обновлениями безопасности!
