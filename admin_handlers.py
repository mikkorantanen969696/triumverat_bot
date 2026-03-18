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

class AdminHandlers:
    """Класс с обработчиками для администратора"""
    
    @staticmethod
    async def remove_manager(callback: CallbackQuery, state: FSMContext):
        """Удаление менеджера"""
        await callback.message.edit_text("➖ Введите Telegram ID менеджера для удаления:")
        await state.set_state("waiting_remove_manager_id")
    
    @staticmethod
    async def process_remove_manager_id(message: Message, state: FSMContext):
        """Обработка ID менеджера для удаления"""
        try:
            manager_id = int(message.text)
            user = await db.get_user_by_telegram_id(manager_id)
            
            if user and user.role == UserRole.MANAGER:
                await db.update_user_role(user.id, UserRole.CLIENT)
                
                # Удаляем пароль из конфига
                if manager_id in settings.MANAGER_PASSWORDS:
                    del settings.MANAGER_PASSWORDS[manager_id]
                
                await message.answer(f"✅ Менеджер {user.full_name or user.username} успешно удален!")
            else:
                await message.answer("❌ Менеджер с таким ID не найден")
            
            await state.clear()
            
        except ValueError:
            await message.answer("❌ Некорректный ID. Пожалуйста, введите число:")
    
    @staticmethod
    async def export_data(callback: CallbackQuery):
        """Выгрузка данных"""
        await callback.message.edit_text(
            "📤 Выберите формат выгрузки данных:",
            reply_markup=get_export_keyboard()
        )
    
    @staticmethod
    async def export_excel(callback: CallbackQuery):
        """Выгрузка в Excel"""
        await callback.answer("📊 Подготовка Excel файла...", show_alert=True)
        
        # Здесь будет логика выгрузки в Excel
        # Для примера отправляем сообщение
        await callback.message.answer(
            "📊 Excel файл готов!\n\n"
            "Функция будет реализована в полной версии.\n"
            "Содержимое: все заявки, пользователи, платежи, статистика."
        )
    
    @staticmethod
    async def export_csv(callback: CallbackQuery):
        """Выгрузка в CSV"""
        await callback.answer("📄 Подготовка CSV файла...", show_alert=True)
        
        # Здесь будет логика выгрузки в CSV
        await callback.message.answer(
            "📄 CSV файл готов!\n\n"
            "Функция будет реализована в полной версии.\n"
            "Содержимое: все заявки, пользователи, платежи, статистика."
        )
    
    @staticmethod
    async def manage_payments(callback: CallbackQuery):
        """Управление платежами"""
        await callback.message.edit_text(
            "💰 Управление платежами:",
            reply_markup=get_payment_keyboard()
        )
    
    @staticmethod
    async def pay_cleaner(callback: CallbackQuery):
        """Оплата клинеру"""
        await callback.message.edit_text(
            "💰 Выберите клинера для оплаты:\n\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показан список клинеров с невыплаченными заказами."
        )
    
    @staticmethod
    async def receive_payment(callback: CallbackQuery):
        """Получение оплаты от клиента"""
        await callback.message.edit_text(
            "💳 Получение оплаты от клиента:\n\n"
            "Функция будет реализована в полной версии.\n"
            "Будет возможность отметить оплату от клиента."
        )
    
    @staticmethod
    async def payment_history(callback: CallbackQuery):
        """История платежей"""
        await callback.message.edit_text(
            "📊 История платежей:\n\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показана история всех платежей с фильтрами."
        )
    
    @staticmethod
    async def city_stats(callback: CallbackQuery):
        """Статистика по городам"""
        stats = await db.get_admin_statistics()
        
        text = "🏙️ <b>СТАТИСТИКА ПО ГОРОДАМ</b>\n\n"
        
        for city_stat in stats.get('city_stats', []):
            text += f"📍 {city_stat['city']}\n"
            text += f"   📋 Заявок: {city_stat['requests_count']}\n"
            text += f"   💰 Выручка: {city_stat['total_revenue']:.2f} руб.\n\n"
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    
    @staticmethod
    async def cleaner_stats(callback: CallbackQuery):
        """Статистика по клинерам"""
        stats = await db.get_admin_statistics()
        
        text = "👨‍🔧 <b>СТАТИСТИКА ПО КЛИНЕРАМ</b>\n\n"
        
        for cleaner_stat in stats.get('cleaner_stats', []):
            text += f"👤 {cleaner_stat['full_name']}\n"
            text += f"   ✅ Выполнено: {cleaner_stat['completed_requests']} заявок\n"
            text += f"   💰 Заработано: {cleaner_stat['total_earned']:.2f} руб.\n\n"
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    
    @staticmethod
    async def manager_stats(callback: CallbackQuery):
        """Статистика по менеджерам"""
        stats = await db.get_admin_statistics()
        
        text = "👥 <b>СТАТИСТИКА ПО МЕНЕДЖЕРАМ</b>\n\n"
        
        for manager_stat in stats.get('manager_stats', []):
            text += f"👤 {manager_stat['full_name']}\n"
            text += f"   📋 Создано: {manager_stat['requests_count']} заявок\n"
            text += f"   💰 Выручка: {manager_stat['total_revenue']:.2f} руб.\n\n"
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    
    @staticmethod
    async def settings_menu(callback: CallbackQuery):
        """Меню настроек"""
        await callback.message.edit_text(
            "⚙️ <b>НАСТРОЙКИ</b>\n\n"
            "Здесь будут доступны настройки системы:\n"
            "• Управление городами\n"
            "• Настройка комиссий\n"
            "• Редактирование реквизитов\n"
            "• Резервное копирование\n\n"
            "Функция будет реализована в полной версии.",
            reply_markup=get_admin_keyboard()
        )
    
    @staticmethod
    async def finances_menu(message: Message):
        """Меню финансов"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        if user.role != UserRole.ADMIN:
            await message.answer("❌ У вас нет прав для выполнения этой команды")
            return
        
        text = """
💰 <b>ФИНАНСЫ</b>

📊 Общая статистика:
• Общая выручка: рассчитывается
• Выплаты клинерам: рассчитывается
• Прибыль: рассчитывается

🔧 Действия:
• Оплатить клинеру
• Получить оплату от клиента
• История платежей
• Финансовый отчет

Выберите действие в меню выше 👆
"""
        
        await message.answer(text, reply_markup=get_admin_keyboard())
