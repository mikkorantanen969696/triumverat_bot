from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import UserRole, CleaningType, RequestStatus

# Главное меню для разных ролей
def get_main_menu(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Управление менеджерами")],
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="📋 Создать заявку")],
                [KeyboardButton(text="💰 Финансы")],
                [KeyboardButton(text="⚙️ Настройки")],
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    elif role == UserRole.MANAGER:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Создать заявку")],
                [KeyboardButton(text="📊 Моя статистика")],
                [KeyboardButton(text="💳 Реквизиты")],
                [KeyboardButton(text="💰 Оплатить клинеру")],
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    else:  # CLEANER
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Доступные заявки")],
                [KeyboardButton(text="🔄 Мои заявки")],
                [KeyboardButton(text="💳 Мои реквизиты")],
            ],
            resize_keyboard=True,
            input_field_placeholder="Выберите действие..."
        )
    
    return keyboard

# Клавиатура авторизации
def get_auth_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔐 Ввести пароль", callback_data="enter_password"))
    return builder.as_markup()

# Клавиатура для администратора
def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="add_manager"),
        InlineKeyboardButton(text="➖ Удалить менеджера", callback_data="remove_manager")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Полная статистика", callback_data="full_stats"),
        InlineKeyboardButton(text="📈 Статистика по менеджерам", callback_data="manager_stats")
    )
    builder.row(
        InlineKeyboardButton(text="🏙️ Статистика по городам", callback_data="city_stats"),
        InlineKeyboardButton(text="👨‍🔧 Статистика по клинерам", callback_data="cleaner_stats")
    )
    builder.row(
        InlineKeyboardButton(text="💳 Управление платежами", callback_data="manage_payments"),
        InlineKeyboardButton(text="📤 Выгрузить данные", callback_data="export_data")
    )
    return builder.as_markup()

# Клавиатура для менеджера
def get_manager_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Создать заявку", callback_data="create_request"),
        InlineKeyboardButton(text="📊 Моя статистика", callback_data="manager_stats")
    )
    builder.row(
        InlineKeyboardButton(text="💳 Реквизиты компании", callback_data="company_requisites"),
        InlineKeyboardButton(text="💰 Оплатить клинеру", callback_data="pay_cleaner")
    )
    builder.row(
        InlineKeyboardButton(text="📤 Выгрузить отчет", callback_data="export_report")
    )
    return builder.as_markup()

# Клавиатура для клинера
def get_cleaner_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Доступные заявки", callback_data="available_requests"),
        InlineKeyboardButton(text="🔄 Мои заявки", callback_data="my_requests")
    )
    builder.row(
        InlineKeyboardButton(text="💳 Мои реквизиты", callback_data="my_requisites")
    )
    return builder.as_markup()

# Клавиатура выбора города
def get_city_keyboard(cities: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for city in cities:
        builder.add(InlineKeyboardButton(text=city, callback_data=f"city_{city}"))
    builder.adjust(2)
    return builder.as_markup()

# Клавиатура выбора типа уборки
def get_cleaning_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🧹 Регулярная уборка", callback_data=f"cleaning_{CleaningType.REGULAR.value}"),
        InlineKeyboardButton(text="🏠 Генеральная уборка", callback_data=f"cleaning_{CleaningType.GENERAL.value}")
    )
    builder.row(
        InlineKeyboardButton(text="🔨 После ремонта", callback_data=f"cleaning_{CleaningType.POST_CONSTRUCTION.value}"),
        InlineKeyboardButton(text="🪟 Мытье окон", callback_data=f"cleaning_{CleaningType.WINDOW.value}")
    )
    builder.row(
        InlineKeyboardButton(text="👔 Химчистка", callback_data=f"cleaning_{CleaningType.DRY_CLEANING.value}")
    )
    return builder.as_markup()

# Клавиатура для заявки
def get_request_keyboard(request_id: int, status: RequestStatus) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if status == RequestStatus.OPEN:
        builder.add(InlineKeyboardButton(text="✅ Взять заявку", callback_data=f"take_request_{request_id}"))
    elif status == RequestStatus.IN_PROGRESS:
        builder.row(
            InlineKeyboardButton(text="📸 Фото ДО", callback_data=f"photo_before_{request_id}"),
            InlineKeyboardButton(text="📸 Фото ПОСЛЕ", callback_data=f"photo_after_{request_id}")
        )
        builder.add(InlineKeyboardButton(text="✅ Завершить заявку", callback_data=f"complete_request_{request_id}"))
    
    builder.add(InlineKeyboardButton(text="📞 Связаться с менеджером", callback_data=f"contact_manager_{request_id}"))
    return builder.as_markup()

# Клавиатура подтверждения
def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"),
        InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_{action}_{item_id}")
    )
    return builder.as_markup()

# Клавиатура для управления заявками (админ/менеджер)
def get_request_management_keyboard(request_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Детали заявки", callback_data=f"request_details_{request_id}"),
        InlineKeyboardButton(text="📸 Фотоотчет", callback_data=f"request_photos_{request_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💳 Создать счет", callback_data=f"create_invoice_{request_id}"),
        InlineKeyboardButton(text="💰 Оплатить клинеру", callback_data=f"pay_cleaner_{request_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отменить заявку", callback_data=f"cancel_request_{request_id}")
    )
    return builder.as_markup()

# Клавиатура для статистики
def get_stats_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_general"),
        InlineKeyboardButton(text="📈 За месяц", callback_data="stats_month")
    )
    builder.row(
        InlineKeyboardButton(text="📉 За неделю", callback_data="stats_week"),
        InlineKeyboardButton(text="📤 Выгрузить", callback_data="export_stats")
    )
    return builder.as_markup()

# Клавиатура для управления платежами
def get_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Оплатить клинеру", callback_data="pay_cleaner"),
        InlineKeyboardButton(text="💳 Получить оплату от клиента", callback_data="receive_payment")
    )
    builder.row(
        InlineKeyboardButton(text="📊 История платежей", callback_data="payment_history")
    )
    return builder.as_markup()

# Клавиатура для экспорта данных
def get_export_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
        InlineKeyboardButton(text="📄 CSV", callback_data="export_csv")
    )
    builder.row(
        InlineKeyboardButton(text="📋 JSON", callback_data="export_json"),
        InlineKeyboardButton(text="📈 PDF отчет", callback_data="export_pdf")
    )
    return builder.as_markup()

# Клавиатура отмены действия
def get_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()
