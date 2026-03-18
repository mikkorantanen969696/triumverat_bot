import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, ReplyKeyboardMarkup

from config import settings
from database_manager import db
from database import UserRole, CleaningType, RequestStatus
from keyboards import *
from utils import *

# Состояния для FSM
class AuthState(StatesGroup):
    waiting_password = State()

class CreateRequestState(StatesGroup):
    waiting_city = State()
    waiting_address = State()
    waiting_client_name = State()
    waiting_client_phone = State()
    waiting_date_time = State()
    waiting_cleaning_type = State()
    waiting_duration = State()
    waiting_price = State()
    waiting_equipment = State()
    waiting_supplies = State()
    waiting_additional_info = State()

class AddManagerState(StatesGroup):
    waiting_manager_id = State()
    waiting_manager_username = State()
    waiting_manager_password = State()

# Инициализация бота
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Хранилище для временных данных
user_data: Dict[int, Dict[str, Any]] = {}

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        # Новый пользователь - регистрация
        await message.answer(
            "👋 Добро пожаловать в систему управления клинингом!\n\n"
            "Пожалуйста, введите ваш пароль для авторизации:",
            reply_markup=get_auth_keyboard()
        )
        await state.set_state(AuthState.waiting_password)
    else:
        # Существующий пользователь
        await show_main_menu(message, user.role)

async def show_main_menu(message: Message, role: UserRole):
    """Показывает главное меню в зависимости от роли"""
    if role == UserRole.ADMIN:
        text = "👑 Добро пожаловать, Администратор!"
        reply_markup = get_main_menu(UserRole.ADMIN)
    elif role == UserRole.MANAGER:
        text = "👋 Добро пожаловать, Менеджер!"
        reply_markup = get_main_menu(UserRole.MANAGER)
    else:
        text = "👋 Добро пожаловать, Клинер!"
        reply_markup = get_main_menu(UserRole.CLIENT)
    
    await message.answer(text, reply_markup=reply_markup)

@dp.callback_query(F.data == "enter_password")
async def process_enter_password(callback: CallbackQuery, state: FSMContext):
    """Обработчик ввода пароля"""
    await callback.message.edit_text("🔐 Пожалуйста, введите ваш пароль:")
    await state.set_state(AuthState.waiting_password)

@dp.message(AuthState.waiting_password)
async def process_password(message: Message, state: FSMContext):
    """Обработка введенного пароля"""
    password = message.text.strip()
    user_id = message.from_user.id
    
    # Проверка паролей админа
    if validate_password(user_id, password, "admin"):
        user = await db.get_user_by_telegram_id(user_id)
        if not user:
            user = await db.create_user(user_id, message.from_user.username, UserRole.ADMIN)
        else:
            await db.update_user_role(user.id, UserRole.ADMIN)
        
        await message.answer("✅ Авторизация успешна! Добро пожаловать, Администратор!", 
                           reply_markup=get_main_menu(UserRole.ADMIN))
        await state.clear()
        return
    
    # Проверка паролей менеджера
    if validate_password(user_id, password, "manager"):
        user = await db.get_user_by_telegram_id(user_id)
        if not user:
            user = await db.create_user(user_id, message.from_user.username, UserRole.MANAGER)
        else:
            await db.update_user_role(user.id, UserRole.MANAGER)
        
        await message.answer("✅ Авторизация успешна! Добро пожаловать, Менеджер!", 
                           reply_markup=get_main_menu(UserRole.MANAGER))
        await state.clear()
        return
    
    # Если пароль не найден, регистрируем как клинера
    user = await db.get_user_by_telegram_id(user_id)
    if not user:
        user = await db.create_user(user_id, message.from_user.username, UserRole.CLIENT)
    
    await message.answer("✅ Вы зарегистрированы как клинер!", 
                       reply_markup=get_main_menu(UserRole.CLIENT))
    await state.clear()

# Обработчики для Администратора
@dp.message(F.text == "👥 Управление менеджерами")
async def admin_manage_managers(message: Message):
    """Управление менеджерами"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user.role != UserRole.ADMIN:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    managers = await db.get_all_managers()
    if not managers:
        text = "📭 Список менеджеров пуст"
    else:
        text = "👥 <b>Список менеджеров:</b>\n\n"
        for manager in managers:
            text += f"• {manager.full_name or manager.username} (@{manager.username})\n"
    
    await message.answer(text, reply_markup=get_admin_keyboard())

@dp.callback_query(F.data == "add_manager")
async def admin_add_manager(callback: CallbackQuery, state: FSMContext):
    """Добавление менеджера"""
    await callback.message.edit_text("➕ Введите Telegram ID нового менеджера:")
    await state.set_state(AddManagerState.waiting_manager_id)

@dp.message(AddManagerState.waiting_manager_id)
async def process_manager_id(message: Message, state: FSMContext):
    """Обработка ID менеджера"""
    try:
        manager_id = int(message.text)
        await state.update_data(manager_id=manager_id)
        await message.answer("➡️ Теперь введите username менеджера (без @):")
        await state.set_state(AddManagerState.waiting_manager_username)
    except ValueError:
        await message.answer("❌ Некорректный ID. Пожалуйста, введите число:")

@dp.message(AddManagerState.waiting_manager_username)
async def process_manager_username(message: Message, state: FSMContext):
    """Обработка username менеджера"""
    username = message.text.strip().lstrip('@')
    await state.update_data(username=username)
    await message.answer("➡️ Теперь введите пароль для менеджера:")
    await state.set_state(AddManagerState.waiting_manager_password)

@dp.message(AddManagerState.waiting_manager_password)
async def process_manager_password(message: Message, state: FSMContext):
    """Обработка пароля менеджера"""
    data = await state.get_data()
    password = message.text.strip()
    
    # Добавляем пароль в конфиг
    settings.MANAGER_PASSWORDS[data['manager_id']] = password
    
    # Создаем пользователя
    user = await db.get_user_by_telegram_id(data['manager_id'])
    if not user:
        await db.create_user(data['manager_id'], data['username'], UserRole.MANAGER)
    else:
        await db.update_user_role(user.id, UserRole.MANAGER)
    
    await message.answer(f"✅ Менеджер @{data['username']} успешно добавлен!\n"
                        f"ID: {data['manager_id']}\n"
                        f"Пароль: {password}")
    await state.clear()

@dp.callback_query(F.data == "full_stats")
async def admin_full_stats(callback: CallbackQuery):
    """Полная статистика для админа"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user.role != UserRole.ADMIN:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    stats = await db.get_admin_statistics()
    text = format_statistics(stats, "admin")
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())

# Обработчики для Менеджера
@dp.message(F.text == "📋 Создать заявку")
async def manager_create_request(message: Message, state: FSMContext):
    """Начало создания заявки"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return
    
    await message.answer("🏙️ Выберите город:", reply_markup=get_city_keyboard(list(settings.CITIES.keys())))
    await state.set_state(CreateRequestState.waiting_city)

@dp.callback_query(F.data.startswith("city_"))
async def process_city_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора города"""
    city = callback.data.split('_', 1)[1]
    await state.update_data(city=city)
    await callback.message.edit_text(f"📍 Город: {city}\n\n🏠 Введите адрес уборки:")
    await state.set_state(CreateRequestState.waiting_address)

@dp.message(CreateRequestState.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса"""
    await state.update_data(address=message.text)
    await message.answer("👤 Введите имя клиента:")
    await state.set_state(CreateRequestState.waiting_client_name)

@dp.message(CreateRequestState.waiting_client_name)
async def process_client_name(message: Message, state: FSMContext):
    """Обработка имени клиента"""
    await state.update_data(client_name=message.text)
    await message.answer("📞 Введите телефон клиента:")
    await state.set_state(CreateRequestState.waiting_client_phone)

@dp.message(CreateRequestState.waiting_client_phone)
async def process_client_phone(message: Message, state: FSMContext):
    """Обработка телефона клиента"""
    phone = message.text.strip()
    if not validate_phone(phone):
        await message.answer("❌ Некорректный номер телефона. Попробуйте еще раз:")
        return
    
    await state.update_data(client_phone=phone)
    await message.answer("📅 Введите дату и время уборки (формат: ДД.ММ.ГГГГ ЧЧ:ММ):")
    await state.set_state(CreateRequestState.waiting_date_time)

@dp.message(CreateRequestState.waiting_date_time)
async def process_date_time(message: Message, state: FSMContext):
    """Обработка даты и времени"""
    try:
        date_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(date_time=date_time)
        await message.answer("🧹 Выберите тип уборки:", reply_markup=get_cleaning_type_keyboard())
        await state.set_state(CreateRequestState.waiting_cleaning_type)
    except ValueError:
        await message.answer("❌ Некорректный формат. Используйте: ДД.ММ.ГГГГ ЧЧ:ММ")

@dp.callback_query(F.data.startswith("cleaning_"))
async def process_cleaning_type(callback: CallbackQuery, state: FSMContext):
    """Обработка типа уборки"""
    cleaning_type = callback.data.split('_', 1)[1]
    await state.update_data(cleaning_type=cleaning_type)
    await callback.message.edit_text(f"🧹 Тип уборки: {cleaning_type}\n\n⏱️ Введите продолжительность (в часах):")
    await state.set_state(CreateRequestState.waiting_duration)

@dp.message(CreateRequestState.waiting_duration)
async def process_duration(message: Message, state: FSMContext):
    """Обработка продолжительности"""
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer("❌ Продолжительность должна быть положительным числом:")
            return
        
        await state.update_data(estimated_duration=duration)
        await message.answer("💰 Введите стоимость заказа (в рублях):")
        await state.set_state(CreateRequestState.waiting_price)
    except ValueError:
        await message.answer("❌ Введите целое число:")

@dp.message(CreateRequestState.waiting_price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    try:
        price = float(message.text)
        if price <= 0:
            await message.answer("❌ Цена должна быть положительным числом:")
            return
        
        await state.update_data(price=price)
        await message.answer("🔧 Оборудование на месте? (Да/Нет):")
        await state.set_state(CreateRequestState.waiting_equipment)
    except ValueError:
        await message.answer("❌ Введите число:")

@dp.message(CreateRequestState.waiting_equipment)
async def process_equipment(message: Message, state: FSMContext):
    """Обработка наличия оборудования"""
    equipment = message.text.lower() in ['да', 'yes', 'y', 'д']
    await state.update_data(equipment_available=equipment)
    await message.answer("🧽 Моющие средства на месте? (Да/Нет):")
    await state.set_state(CreateRequestState.waiting_supplies)

@dp.message(CreateRequestState.waiting_supplies)
async def process_supplies(message: Message, state: FSMContext):
    """Обработка наличия моющих средств"""
    supplies = message.text.lower() in ['да', 'yes', 'y', 'д']
    await state.update_data(cleaning_supplies_available=supplies)
    await message.answer("📝 Дополнительная информация (необязательно):")
    await state.set_state(CreateRequestState.waiting_additional_info)

@dp.message(CreateRequestState.waiting_additional_info)
async def process_additional_info(message: Message, state: FSMContext):
    """Обработка дополнительной информации и создание заявки"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    
    # Создание заявки
    request_data = {
        'manager_id': user.id,
        'city': data['city'],
        'address': data['address'],
        'client_name': data['client_name'],
        'client_phone': data['client_phone'],
        'date_time': data['date_time'],
        'cleaning_type': data['cleaning_type'],
        'estimated_duration': data['estimated_duration'],
        'price': data['price'],
        'equipment_available': data['equipment_available'],
        'cleaning_supplies_available': data['cleaning_supplies_available'],
        'additional_info': message.text if message.text.strip() else None
    }
    
    request = await db.create_request(request_data)
    
    # Формирование сообщения о созданной заявке
    text = f"""
✅ <b>Заявка успешно создана!</b>

🔢 Номер: #{request.id}
🏙️ Город: {request.city}
📍 Адрес: {request.address}
👤 Клиент: {request.client_name}
📞 Телефон: {format_phone(request.client_phone)}
📅 Дата и время: {format_datetime(request.date_time)}
🧹 Тип уборки: {request.cleaning_type}
⏱️ Продолжительность: {request.estimated_duration} часов
💰 Стоимость: {request.price:.2f} руб.
🔧 Оборудование: {'Есть' if request.equipment_available else 'Нет'}
🧽 Моющие средства: {'Есть' if request.cleaning_supplies_available else 'Нет'}
"""
    
    if request.additional_info:
        text += f"📝 Доп. информация: {request.additional_info}"
    
    await message.answer(text, reply_markup=get_main_menu(user.role))
    await state.clear()

# Обработчики для Клинера
@dp.message(F.text == "📋 Доступные заявки")
async def cleaner_available_requests(message: Message):
    """Показ доступных заявок для клинера"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if user.role != UserRole.CLIENT:
        await message.answer("❌ Эта функция доступна только клинерам")
        return
    
    requests = await db.get_open_requests_by_city(user.city or "")
    
    if not requests:
        await message.answer("📭 В вашем городе пока нет доступных заявок")
        return
    
    for request in requests:
        text = f"""
{get_status_emoji(request.status.value)} <b>Заявка #{request.id}</b>

📍 Адрес: {request.address}
👤 Клиент: {request.client_name}
📅 Дата и время: {format_datetime(request.date_time)}
🧹 Тип уборки: {request.cleaning_type}
⏱️ Продолжительность: {request.estimated_duration} часов
💰 Стоимость: {request.price:.2f} руб.
"""
        
        keyboard = get_request_keyboard(request.id, request.status)
        await message.answer(text, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("take_request_"))
async def cleaner_take_request(callback: CallbackQuery):
    """Клинер берет заявку"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    if user.role != UserRole.CLIENT:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    request_id = int(callback.data.split('_')[-1])
    success = await db.assign_request_to_cleaner(request_id, user.id)
    
    if success:
        await callback.answer("✅ Заявка принята!", show_alert=True)
        await callback.message.edit_text("✅ Вы взяли эту заявку!")
        
        # Отправляем информацию менеджеру
        request = await db.get_request_by_id(request_id)
        if request:
            manager = await db.get_user_by_id(request.manager_id)
            if manager:
                await bot.send_message(
                    manager.telegram_id,
                    f"🎉 Заявку #{request_id} взял клинер {user.full_name or user.username}!\n"
                    f"📞 Телефон клинера: {user.phone or 'Не указан'}"
                )
    else:
        await callback.answer("❌ Не удалось взять заявку", show_alert=True)

# Основная функция запуска
async def main():
    # Создаем директории
    create_directories()
    
    # Инициализируем базу данных
    await db.init_db()
    
    # Запускаем бота
    logger.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
