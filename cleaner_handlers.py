from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import logging

from database_manager import db
from database import UserRole, RequestStatus
from keyboards import *
from utils import *
from bot import bot

logger = logging.getLogger(__name__)

class CleanerHandlers:
    """Класс с обработчиками для клинера"""
    
    @staticmethod
    async def my_requests(message: Message):
        """Мои заявки"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        requests = await db.get_requests_by_cleaner(user.id)
        
        if not requests:
            await message.answer("📭 У вас пока нет заявок")
            return
        
        text = f"🔄 <b>МОИ ЗАЯВКИ</b> ({len(requests)} шт.)\n\n"
        
        for request in requests:
            status_emoji = get_status_emoji(request.status.value)
            cleaning_emoji = get_cleaning_type_emoji(request.cleaning_type.value)
            
            text += f"{status_emoji} <b>#{request.id}</b> {cleaning_emoji}\n"
            text += f"📍 {request.address}\n"
            text += f"👤 {request.client_name} | 📞 {format_phone(request.client_phone)}\n"
            text += f"📅 {format_datetime(request.date_time)} | 💰 {request.price:.2f} руб.\n\n"
        
        await message.answer(text, reply_markup=get_main_menu(UserRole.CLIENT))
    
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
    async def contact_manager(callback: CallbackQuery):
        """Связаться с менеджером"""
        request_id = int(callback.data.split('_')[-1])
        
        await callback.message.edit_text(
            f"📞 <b>СВЯЗЬ С МЕНЕДЖЕРОМ</b>\n\n"
            f"Заявка #{request_id}\n"
            "Функция будет реализована в полной версии.\n"
            "Будет показана контактная информация менеджера."
        )
    
    @staticmethod
    async def upload_photo_before(callback: CallbackQuery, state: FSMContext):
        """Загрузка фото ДО"""
        request_id = int(callback.data.split('_')[-1])
        await state.update_data(request_id=request_id, photo_type="before")
        
        await callback.message.edit_text(
            f"📸 <b>ЗАГРУЗКА ФОТО ДО</b>\n\n"
            f"Заявка #{request_id}\n\n"
            "Пожалуйста, сделайте фотографии обстановки до начала уборки "
            "и отправьте их сюда. Можно отправить несколько фото."
        )
        await state.set_state("waiting_photo")
    
    @staticmethod
    async def upload_photo_after(callback: CallbackQuery, state: FSMContext):
        """Загрузка фото ПОСЛЕ"""
        request_id = int(callback.data.split('_')[-1])
        await state.update_data(request_id=request_id, photo_type="after")
        
        await callback.message.edit_text(
            f"📸 <b>ЗАГРУЗКА ФОТО ПОСЛЕ</b>\n\n"
            f"Заявка #{request_id}\n\n"
            "Пожалуйста, сделайте фотографии обстановки после завершения уборки "
            "и отправьте их сюда. Можно отправить несколько фото."
        )
        await state.set_state("waiting_photo")
    
    @staticmethod
    async def process_photo(message: Message, state: FSMContext):
        """Обработка загруженного фото"""
        if not message.photo:
            await message.answer("❌ Пожалуйста, отправьте фото")
            return
        
        data = await state.get_data()
        request_id = data.get('request_id')
        photo_type = data.get('photo_type')
        
        if not request_id or not photo_type:
            await message.answer("❌ Ошибка состояния. Попробуйте еще раз")
            return
        
        # Сохранение фото
        file_id = message.photo[-1].file_id
        await db.add_request_photo(request_id, file_id, photo_type)
        
        await message.answer(f"✅ Фото '{photo_type}' успешно загружено!")
        
        # Показываем загруженные фото
        photos = await db.get_request_photos(request_id)
        before_photos = [p for p in photos if p.photo_type == "before"]
        after_photos = [p for p in photos if p.photo_type == "after"]
        
        text = f"📸 <b>ФОТОАЛЬБОМ ЗАЯВКИ #{request_id}</b>\n\n"
        text += f"📸 Фото ДО: {len(before_photos)} шт.\n"
        text += f"📸 Фото ПОСЛЕ: {len(after_photos)} шт.\n\n"
        
        if len(before_photos) > 0 and len(after_photos) > 0:
            text += "✅ Все фото загружены! Заявку можно завершать."
        
        await message.answer(text)
    
    @staticmethod
    async def complete_request(callback: CallbackQuery):
        """Завершение заявки"""
        request_id = int(callback.data.split('_')[-1])
        
        # Проверяем наличие фото
        photos = await db.get_request_photos(request_id)
        before_photos = [p for p in photos if p.photo_type == "before"]
        after_photos = [p for p in photos if p.photo_type == "after"]
        
        if len(before_photos) == 0 or len(after_photos) == 0:
            await callback.answer(
                "❌ Сначала загрузите фото ДО и ПОСЛЕ!",
                show_alert=True
            )
            return
        
        await callback.message.edit_text(
            f"✅ <b>ЗАВЕРШЕНИЕ ЗАЯВКИ #{request_id}</b>\n\n"
            "Вы уверены, что хотите завершить заявку?\n"
            "После завершения заявка будет закрыта и отправлена на проверку.",
            reply_markup=get_confirmation_keyboard("complete_request", request_id)
        )
    
    @staticmethod
    async def confirm_complete_request(callback: CallbackQuery):
        """Подтверждение завершения заявки"""
        request_id = int(callback.data.split('_')[-1])
        
        success = await db.complete_request(request_id)
        
        if success:
            await callback.message.edit_text(
                f"✅ Заявка #{request_id} успешно завершена!\n\n"
                "Ожидайте подтверждения от менеджера и оплаты."
            )
            
            # Уведомляем менеджера
            request = await db.get_request_by_id(request_id)
            if request and request.manager_id:
                manager = await db.get_user_by_id(request.manager_id)
                if manager:
                    await bot.send_message(
                        manager.telegram_id,
                        f"✅ Заявка #{request_id} выполнена клинером!\n\n"
                        f"📍 Адрес: {request.address}\n"
                        f"💰 Сумма к оплате клинеру: {request.price:.2f} руб.\n\n"
                        "Пожалуйста, проверьте фотоотчет и оплатите услуги клинера."
                    )
        else:
            await callback.message.edit_text(
                "❌ Не удалось завершить заявку. Попробуйте еще раз."
            )
    
    @staticmethod
    async def my_requisites(callback: CallbackQuery):
        """Мои реквизиты"""
        await callback.message.edit_text(
            "💳 <b>МОИ РЕКВИЗИТЫ</b>\n\n"
            "Здесь вы можете указать свои реквизиты для получения оплаты:\n\n"
            "• Номер карты\n"
            "• ФИО получателя\n"
            "• Банк получателя\n\n"
            "Функция будет реализована в полной версии.\n"
            "Реквизиты будут использоваться для автоматических выплат."
        )
    
    @staticmethod
    async def update_requisites(message: Message):
        """Обновление реквизитов"""
        await message.answer(
            "💳 <b>ОБНОВЛЕНИЕ РЕКВИЗИТОВ</b>\n\n"
            "Пожалуйста, введите ваши реквизиты в следующем формате:\n\n"
            "ФИО:\n"
            "Номер карты:\n"
            "Банк:\n\n"
            "Функция будет реализована в полной версии."
        )
    
    @staticmethod
    async def view_earnings(message: Message):
        """Просмотр заработка"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        requests = await db.get_requests_by_cleaner(user.id)
        
        completed_requests = [r for r in requests if r.status == RequestStatus.COMPLETED]
        total_earned = sum(r.price for r in completed_requests)
        
        text = f"💰 <b>МОЙ ЗАРАБОТОК</b>\n\n"
        text += f"✅ Выполнено заявок: {len(completed_requests)}\n"
        text += f"💰 Всего заработано: {total_earned:.2f} руб.\n\n"
        
        if completed_requests:
            text += "<b>Последние выполненные заявки:</b>\n"
            for request in completed_requests[-5:]:
                text += f"• #{request.id} - {request.price:.2f} руб. - {format_datetime(request.completed_at)}\n"
        
        await message.answer(text, reply_markup=get_main_menu(UserRole.CLIENT))
    
    @staticmethod
    async def view_schedule(message: Message):
        """Просмотр расписания"""
        user = await db.get_user_by_telegram_id(message.from_user.id)
        requests = await db.get_requests_by_cleaner(user.id)
        
        active_requests = [r for r in requests if r.status.value in ['in_progress']]
        
        if not active_requests:
            await message.answer("📅 У вас нет активных заявок")
            return
        
        text = "📅 <b>МОЕ РАСПИСАНИЕ</b>\n\n"
        
        for request in active_requests:
            text += f"🔄 {format_datetime(request.date_time)}\n"
            text += f"📍 {request.address}\n"
            text += f"👤 {request.client_name}\n"
            text += f"💰 {request.price:.2f} руб.\n\n"
        
        await message.answer(text, reply_markup=get_main_menu(UserRole.CLIENT))
