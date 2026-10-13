from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


BTN_BACK_MENU = "⬅️ Назад в меню"
BTN_REGENERATE = "🔁 Сгенерировать еще"
BTN_CHANGE_DESCRIPTION = "✏️ Изменить описание"

MENU_SWEET_REPLY = "💌 Ответить мило"
MENU_VIDEOS = "🎬 Любовные видео"
MENU_COUPLE_PHOTOS = "📸 Парные фото"
MENU_DATE = "🌹 Свидание"
MENU_TRAVEL = "✈️ Путешествие"
MENU_COMPLIMENTS = "🥰 Комплименты"
MENU_SITUATION = "🧠 Анализ ситуации"
MENU_WISH = "🎁 Желание"
MENU_DIY = "🧸 Милые идеи своими руками"
MENU_FLOWERS = "💐 Цветы"
MENU_POEMS = "📝 Стихи"
MENU_SETTINGS = "⚙️ Настройки"


def currency_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Тенге ₸ — Казахстан", callback_data="currency:KZT")
    builder.button(text="Рубли ₽ — Россия", callback_data="currency:RUB")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    items = (
        ("menu:sweet_reply", MENU_SWEET_REPLY),
        ("menu:videos", MENU_VIDEOS),
        ("menu:couple_photos", MENU_COUPLE_PHOTOS),
        ("menu:date", MENU_DATE),
        ("menu:travel", MENU_TRAVEL),
        ("menu:compliments", MENU_COMPLIMENTS),
        ("menu:situation", MENU_SITUATION),
        ("menu:wish", MENU_WISH),
        ("menu:diy", MENU_DIY),
        ("menu:flowers", MENU_FLOWERS),
        ("menu:poems", MENU_POEMS),
        ("menu:settings", MENU_SETTINGS),
    )
    builder = InlineKeyboardBuilder()
    for callback_data, text in items:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(1, 1, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")]]
    )


def result_keyboard(section: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_REGENERATE, callback_data=f"regen:{section}")],
            [InlineKeyboardButton(text=BTN_CHANGE_DESCRIPTION, callback_data=f"change:{section}")],
            [InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")],
        ]
    )


def sweet_reply_style_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("sweet_style:Мило", "Мило"),
            ("sweet_style:Романтично", "Романтично"),
            ("sweet_style:С флиртом", "С флиртом"),
            ("sweet_style:Нежно", "Нежно"),
            ("sweet_style:С юмором", "С юмором"),
            ("sweet_style:Извиниться красиво", "Извиниться красиво"),
            ("sweet_style:Поддержать", "Поддержать"),
        )
    )


def videos_target_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("videos_target:Для неё", "Для неё"),
            ("videos_target:Для него", "Для него"),
        )
    )


def couple_photos_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("couple_photos_choice:Готовые идеи", "Готовые идеи"),
            ("couple_photos_choice:Фото своими руками", "Фото своими руками"),
            ("couple_photos_choice:Промт для генерации картинки", "Промт для генерации картинки"),
        )
    )


def date_budget_keyboard(currency_symbol: str) -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("date_budget:free", "Нету денег / своими руками"),
            ("date_budget:up_2500", f"До 2500 {currency_symbol}"),
            ("date_budget:2500_4000", f"2500–4000 {currency_symbol}"),
            ("date_budget:4000_7000", f"4000–7000 {currency_symbol}"),
            ("date_budget:7000_plus", f"7000+ {currency_symbol}"),
            ("date_budget:custom", "Свой бюджет"),
        )
    )


def date_format_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("date_format:Покушать", "Покушать"),
            ("date_format:Погулять", "Погулять"),
            ("date_format:Поиграть", "Поиграть"),
            ("date_format:Романтика дома", "Романтика дома"),
            ("date_format:Активное свидание", "Активное свидание"),
            ("date_format:Сюрприз", "Сюрприз"),
            ("date_format:Смешанный вариант", "Смешанный вариант"),
        )
    )


def travel_type_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("travel_type:Страна", "Страна"),
            ("travel_type:Город", "Город"),
        )
    )


def travel_transport_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("travel_transport:Самолет", "Самолет"),
            ("travel_transport:Поезд", "Поезд"),
            ("travel_transport:Машина", "Машина"),
            ("travel_transport:Автобус", "Автобус"),
        )
    )


def car_consumption_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Использовать 8 л/100 км", callback_data="travel_car:consumption_default")],
            [InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")],
        ]
    )


def fuel_price_keyboard(price: int, symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Использовать {price} {symbol}/л",
                    callback_data="travel_car:fuel_default",
                )
            ],
            [InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")],
        ]
    )


def compliments_target_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("compliments_target:Для неё", "Для неё"),
            ("compliments_target:Для него", "Для него"),
        )
    )


def compliments_style_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("compliments_style:Милые", "Милые"),
            ("compliments_style:Романтичные", "Романтичные"),
            ("compliments_style:Короткие", "Короткие"),
            ("compliments_style:Длинные", "Длинные"),
            ("compliments_style:С флиртом", "С флиртом"),
            ("compliments_style:После ссоры", "После ссоры"),
            ("compliments_style:На утро", "На утро"),
            ("compliments_style:На ночь", "На ночь"),
        )
    )


def situation_goal_keyboard() -> InlineKeyboardMarkup:
    return _single_column_keyboard(
        (
            ("situation_goal:Понять, что делать", "Понять, что делать"),
            ("situation_goal:Написать сообщение", "Написать сообщение"),
            ("situation_goal:Извиниться", "Извиниться"),
            ("situation_goal:Помириться", "Помириться"),
            ("situation_goal:Понять поведение человека", "Понять поведение человека"),
            ("situation_goal:Не испортить отношения", "Не испортить отношения"),
        )
    )


def diy_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Трендовая идея", callback_data="diy:trend")],
            [InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сменить валюту", callback_data="settings:currency")],
            [InlineKeyboardButton(text="Сбросить диалог", callback_data="settings:reset")],
            [InlineKeyboardButton(text="О боте", callback_data="settings:about")],
            [InlineKeyboardButton(text=BTN_BACK_MENU, callback_data="menu")],
        ]
    )


def _single_column_keyboard(items: tuple[tuple[str, str], ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for callback_data, text in items:
        builder.button(text=text, callback_data=callback_data)
    builder.button(text=BTN_BACK_MENU, callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()

