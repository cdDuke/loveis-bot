import logging

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import Settings
from bot.keyboards import currency_keyboard, main_menu_keyboard
from bot.repositories.user_repository import upsert_user
from bot.services.budget_service import currency_name, currency_symbol


logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = (
    "Привет! Я LoveIS 💕\n"
    "Я помогу тебе сделать отношения теплее: подскажу милый ответ, придумаю свидание, "
    "комплимент, стих, букет, путешествие или подарок своими руками.\n"
    "Сначала выбери валюту, чтобы я мог считать бюджеты правильно."
)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    settings: Settings,
) -> None:
    await state.clear()
    await upsert_user(db, message.from_user)

    if settings.start_image_path.exists():
        try:
            await message.answer_photo(
                FSInputFile(settings.start_image_path),
                caption=WELCOME_TEXT,
                reply_markup=currency_keyboard(),
            )
            return
        except Exception:
            logger.exception("Failed to send start image")

    await message.answer(WELCOME_TEXT, reply_markup=currency_keyboard())


@router.message(Command("currency"))
async def cmd_currency(message: Message, state: FSMContext, db: aiosqlite.Connection) -> None:
    await state.clear()
    await upsert_user(db, message.from_user)
    await message.answer(
        "Выбери валюту. Я сохраню ее и буду использовать во всех бюджетах.",
        reply_markup=currency_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "LoveIS — любовный помощник для пар.\n\n"
        "Команды:\n"
        "/start — начать заново\n"
        "/menu — открыть главное меню\n"
        "/currency — сменить валюту\n"
        "/help — помощь\n\n"
        "Выбери раздел в меню, а я аккуратно проведу тебя по шагам."
    )


@router.callback_query(F.data.startswith("currency:"))
async def choose_currency(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    currency = callback.data.split(":", 1)[1]
    await state.clear()
    await upsert_user(db, callback.from_user, currency=currency)
    await callback.answer("Валюта сохранена")

    await callback.message.answer(
        f"Готово: {currency_name(currency)} {currency_symbol(currency)}.\n"
        "Теперь выбери, с чем помочь 💕",
        reply_markup=main_menu_keyboard(),
    )

