from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import logging

from database_manager import db
from database import UserRole
from keyboards import *
from utils import *
from bot import bot

logger = logging.getLogger(__name__)

class ManagerHandlers:
    """Класс с обработчиками для менеджера"""
    
    @staticmethod
    async def manager_stats(callback: CallbackQuery):
        """Статистика менеджера"""
        user = await db.get_user_by_telegram_id(callback.from_user.id)
        stats = await db.get_manager_statistics(user.id)
        
        text = format_statistics(stats, "manager")
        await callback.message.edit_text(text, reply_markup=get_manager_keyboard())
    
    @staticmethod
    async def company_requisites(callback: CallbackQuery):
        """Реквизиты компании"""
        requisites_text = """
💳 <b>РЕКВИЗИТЫ КОМПАНИИ</b>

🏢 ИП Иванов Иван Иванович
📝 ИНН: 123456789012
💳 Расчетный счет: 12345678901234567890
🏦 Банк: ПАО "СБЕРБАНК"
🔢 БИК: 044525225
💵 Корр. счет: 30101810400000000225

📧 Email: info@cleaning.ru
🌐 Сайт: cleaning.ru
📞 Телефон: +7 (495) 123-45-67

⚠️ <b>Важно:</b> При создании счета используйте эти реквизиты.
Все платежи от клиентов должны поступать на этот счет.
"""
        
        await callback.message.edit_text(requisites_text, reply_markup=get_manager_keyboard())
    
    @staticmethod
    async def create_invoice(callback: CallbackQuery):
        """Создание счета для клиента"""
        await callback.message.edit_text(
            "💳 <b>СОЗДАНИЕ СЧЕТА</b>\n\n"
            "Введите номер заявки для создания счета:\n"
            "Функция будет реализована в полной версии.\n"
            "Будет сгенерирован PDF счет с QR кодом для оплаты."
        )
    
    @staticmethod
    async def export_report(callback: CallbackQuery):
        """Выгрузка отчета"""
        await callback.message.edit_text(
            "📤 <b>ВЫГРУЗКА ОТЧЕТА</b>\n\n"
            "Выберите формат отчета:",
            reply_markup=get_export_keyboard()
        )
    
    @staticmethod
    async def my_requests(message: Message):
        """Мои заявки"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        requests = await db.get_requests_by_manager(user.id)
        
        if not requests:
            await message.answer("📭 У вас пока нет созданных заявок")
            return
        
        text = f"📋 <b>ВАШИ ЗАЯВКИ</b> ({len(requests)} шт.)\n\n"
        
        for request in requests[:10]:  # Показываем последние 10
            status_emoji = get_status_emoji(request.status.value)
            cleaning_emoji = get_cleaning_type_emoji(request.cleaning_type.value)
            
            text += f"{status_emoji} <b>#{request.id}</b> {cleaning_emoji}\n"
            text += f"📍 {request.address}\n"
            text += f"👤 {request.client_name} | 📞 {format_phone(request.client_phone)}\n"
            text += f"📅 {format_datetime(request.date_time)} | 💰 {request.price:.2f} руб.\n\n"
        
        await message.answer(text, reply_markup=get_main_menu(UserRole.MANAGER))
    
    @staticmethod
    async def request_details(callback: CallbackQuery):
        """Детали заявки"""
        request_id = int(callback.data.split('_')[-1])
        
        # Здесь будет логика получения деталей заявки
        await callback.message.edit_text(
            f"📋 <b>ДЕТАЛИ ЗАЯВКИ #{request_id}</b>\n\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показана вся информация по заявке."
        )
    
    @staticmethod
    async def contact_cleaner(callback: CallbackQuery):
        """Связаться с клинером"""
        request_id = int(callback.data.split('_')[-1])
        
        await callback.message.edit_text(
            f"📞 <b>СВЯЗЬ С КЛИНЕРОМ</b>\n\n"
            f"Заявка #{request_id}\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показана контактная информация клинера."
        )
    
    @staticmethod
    async def cancel_request(callback: CallbackQuery):
        """Отмена заявки"""
        request_id = int(callback.data.split('_')[-1])
        
        await callback.message.edit_text(
            f"❌ <b>ОТМЕНА ЗАЯВКИ #{request_id}</b>\n\n"
            "Вы уверены, что хотите отменить эту заявку?",
            reply_markup=get_confirmation_keyboard("cancel_request", request_id)
        )
    
    @staticmethod
    async def confirm_cancel_request(callback: CallbackQuery):
        """Подтверждение отмены заявки"""
        request_id = int(callback.data.split('_')[-1])
        
        # Здесь будет логика отмены заявки
        await callback.message.edit_text(
            f"✅ Заявка #{request_id} успешно отменена!"
        )
    
    @staticmethod
    async def pay_cleaner(callback: CallbackQuery):
        """Оплата клинеру"""
        await callback.message.edit_text(
            "💰 <b>ОПЛАТА КЛИНЕРА</b>\n\n"
            "Выберите заявку для оплаты клинеру:\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показан список выполненных заявок с возможностью оплаты."
        )
    
    @staticmethod
    async def send_invoice(callback: CallbackQuery):
        """Отправить счет клиенту"""
        request_id = int(callback.data.split('_')[-1])
        
        await callback.message.edit_text(
            f"💳 <b>ОТПРАВКА СЧЕТА КЛИЕНТУ</b>\n\n"
            f"Заявка #{request_id}\n"
            "Функция будет реализована в полной версии.\n"
            "Будет создан и отправлен PDF счет клиенту."
        )
    
    @staticmethod
    async def view_schedule(message: Message):
        """Просмотр расписания"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        requests = await db.get_requests_by_manager(user.id)
        
        # Фильтруем активные заявки
        active_requests = [r for r in requests if r.status.value in ['open', 'in_progress']]
        
        if not active_requests:
            await message.answer("📅 У вас нет активных заявок")
            return
        
        text = "📅 <b>РАСПИСАНИЕ</b>\n\n"
        
        for request in active_requests:
            status_emoji = get_status_emoji(request.status.value)
            text += f"{status_emoji} {format_datetime(request.date_time)}\n"
            text += f"📍 {request.address}\n"
            text += f"👤 {request.client_name}\n\n"
        
        await message.answer(text, reply_markup=get_main_menu(UserRole.MANAGER))
