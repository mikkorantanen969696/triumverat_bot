import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import qrcode
from io import BytesIO
import base64

from config import settings

# Настройка логирования
def setup_logging():
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Создание директорий
def create_directories():
    os.makedirs(settings.PHOTOS_PATH, exist_ok=True)
    os.makedirs(settings.PDF_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

# Форматирование даты и времени
def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")

# Генерация PDF счета
def generate_invoice(request_data: Dict[str, Any]) -> str:
    """Генерирует PDF счет и возвращает путь к файлу"""
    filename = f"invoice_{request_data['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(settings.PDF_PATH, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Заголовок
    title = Paragraph("СЧЕТ НА ОПЛАТУ", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Информация о заказе
    order_info = f"""
    <b>Номер заказа:</b> #{request_data['id']}<br/>
    <b>Дата создания:</b> {format_datetime(request_data['created_at'])}<br/>
    <b>Клиент:</b> {request_data['client_name']}<br/>
    <b>Телефон:</b> {request_data['client_phone']}<br/>
    <b>Адрес:</b> {request_data['address']}<br/>
    <b>Тип уборки:</b> {request_data['cleaning_type']}<br/>
    <b>Дата и время:</b> {format_datetime(request_data['date_time'])}<br/>
    <b>Продолжительность:</b> {request_data['estimated_duration']} часов<br/>
    <b>Сумма к оплате:</b> {request_data['price']:.2f} руб.
    """
    
    order_para = Paragraph(order_info, styles['Normal'])
    story.append(order_para)
    story.append(Spacer(1, 12))
    
    # Реквизиты компании
    requisites = """
    <b>Реквизиты компании:</b><br/>
    ИП Иванов Иван Иванович<br/>
    ИНН: 123456789012<br/>
    Расчетный счет: 12345678901234567890<br/>
    Банк: ПАО "СБЕРБАНК"<br/>
    БИК: 044525225<br/>
    Корр. счет: 30101810400000000225
    """
    
    req_para = Paragraph(requisites, styles['Normal'])
    story.append(req_para)
    story.append(Spacer(1, 24))
    
    # QR код для оплаты
    qr_data = f"Сумма: {request_data['price']:.2f} руб. Заказ #{request_data['id']}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    doc.build(story)
    
    return filepath

# Валидация пароля
def validate_password(user_id: int, password: str, role: str) -> bool:
    """Проверяет пароль для пользователя"""
    if role == "admin":
        return settings.ADMIN_PASSWORDS.get(user_id) == password
    elif role == "manager":
        return settings.MANAGER_PASSWORDS.get(user_id) == password
    return False

# Форматирование статистики
def format_statistics(stats: Dict[str, Any], role: str = "admin") -> str:
    """Форматирует статистику для вывода"""
    if role == "admin":
        message = f"""
📊 <b>ОБЩАЯ СТАТИСТИКА</b>

📋 Всего заявок: {stats.get('total_requests', 0)}
✅ Выполнено заявок: {stats.get('completed_requests', 0)}
💰 Общая выручка: {stats.get('total_revenue', 0):.2f} руб.

👥 <b>СТАТИСТИКА ПО МЕНЕДЖЕРАМ</b>
"""
        for manager in stats.get('manager_stats', []):
            message += f"\n• {manager['full_name']}: {manager['requests_count']} заявок, {manager['total_revenue']:.2f} руб."
        
        message += "\n\n🏙️ <b>СТАТИСТИКА ПО ГОРОДАМ</b>"
        for city in stats.get('city_stats', []):
            message += f"\n• {city['city']}: {city['requests_count']} заявок, {city['total_revenue']:.2f} руб."
        
        message += "\n\n👨‍🔧 <b>СТАТИСТИКА ПО КЛИНЕРАМ</b>"
        for cleaner in stats.get('cleaner_stats', []):
            message += f"\n• {cleaner['full_name']}: {cleaner['completed_requests']} заявок, {cleaner['total_earned']:.2f} руб."
    
    elif role == "manager":
        message = f"""
📊 <b>ВАША СТАТИСТИКА</b>

📋 Всего создано заявок: {stats.get('total_requests', 0)}
✅ Выполнено заявок: {stats.get('completed_requests', 0)}
💰 Общая выручка: {stats.get('total_revenue', 0):.2f} руб.

📋 <b>ПОСЛЕДНИЕ ЗАЯВКИ</b>
"""
        for req in stats.get('recent_requests', []):
            status_emoji = {"open": "🔵", "in_progress": "🟡", "completed": "🟢", "cancelled": "🔴"}.get(req['status'], "⚪")
            message += f"\n{status_emoji} #{req['id']} - {req['address']} - {req['price']:.2f} руб."
    
    return message

# Безопасное преобразование в int
def safe_int(value: Any, default: int = 0) -> int:
    """Безопасно преобразует значение в int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# Безопасное преобразование в float
def safe_float(value: Any, default: float = 0.0) -> float:
    """Безопасно преобразует значение в float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Проверка корректности телефона
def validate_phone(phone: str) -> bool:
    """Проверяет корректность номера телефона"""
    phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    return len(phone) >= 10 and phone.isdigit()

# Форматирование телефона
def format_phone(phone: str) -> str:
    """Форматирует номер телефона"""
    phone = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    if len(phone) == 10:
        return f"+7 ({phone[:3]}) {phone[3:6]}-{phone[6:8]}-{phone[8:]}"
    elif len(phone) == 11 and phone[0] == '8':
        return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:]}"
    return phone

# Получение эмодзи для статуса
def get_status_emoji(status: str) -> str:
    """Возвращает эмодзи для статуса заявки"""
    status_emojis = {
        "open": "🔵",
        "in_progress": "🟡", 
        "completed": "🟢",
        "cancelled": "🔴"
    }
    return status_emojis.get(status, "⚪")

# Получение эмодзи для типа уборки
def get_cleaning_type_emoji(cleaning_type: str) -> str:
    """Возвращает эмодзи для типа уборки"""
    type_emojis = {
        "regular": "🧹",
        "general": "🏠",
        "post_construction": "🔨",
        "window": "🪟",
        "dry_cleaning": "👔"
    }
    return type_emojis.get(cleaning_type, "🧹")

# Асинхронная обертка для синхронных функций
def async_wrap(func):
    """Декоратор для преобразования синхронных функций в асинхронные"""
    async def run(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return run
