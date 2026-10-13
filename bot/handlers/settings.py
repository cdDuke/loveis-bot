import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards import currency_keyboard, main_menu_keyboard, settings_keyboard
from bot.repositories.user_repository import clear_history


router = Router()


@router.callback_query(F.data == "menu:settings")
async def open_settings(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("⚙️ Настройки LoveIS", reply_markup=settings_keyboard())


@router.callback_query(F.data == "settings:currency")
async def settings_currency(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("Выбери новую валюту:", reply_markup=currency_keyboard())


@router.callback_query(F.data == "settings:reset")
async def settings_reset(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    await state.clear()
    await clear_history(db, callback.from_user.id)
    await callback.answer("Диалог сброшен")
    await callback.message.answer(
        "Готово, я очистил историю запросов и сбросил текущий сценарий.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "settings:about")
async def settings_about(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "LoveIS — твой любовный помощник.\n\n"
        "Я помогаю красиво отвечать, придумывать свидания, комплименты, стихи, букеты, "
        "подарки своими руками, идеи фото и путешествий.\n\n"
        "Я не заменяю специалиста и не даю гарантий по ценам, здоровью, праву или финансам. "
        "В сложных и опасных ситуациях главное — безопасность и поддержка живых людей.",
        reply_markup=settings_keyboard(),
    )

