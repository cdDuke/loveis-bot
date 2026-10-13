import aiosqlite
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import currency_keyboard, main_menu_keyboard
from bot.repositories.user_repository import get_currency, upsert_user


router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, db: aiosqlite.Connection) -> None:
    await state.clear()
    await upsert_user(db, message.from_user)
    currency = await get_currency(db, message.from_user.id)
    if not currency:
        await message.answer("Сначала выбери валюту.", reply_markup=currency_keyboard())
        return

    await message.answer("Главное меню LoveIS 💕", reply_markup=main_menu_keyboard())


@router.callback_query(lambda callback: callback.data == "menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    await state.clear()
    await upsert_user(db, callback.from_user)
    currency = await get_currency(db, callback.from_user.id)
    await callback.answer()

    if not currency:
        await callback.message.answer("Сначала выбери валюту.", reply_markup=currency_keyboard())
        return

    await callback.message.answer("Главное меню LoveIS 💕", reply_markup=main_menu_keyboard())


@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer(
        "Я рядом 💕 Но лучше выбери пункт в меню, чтобы я понял, чем именно помочь.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query()
async def unknown_callback(callback: CallbackQuery) -> None:
    await callback.answer("Кнопка устарела. Открой меню заново.", show_alert=False)
