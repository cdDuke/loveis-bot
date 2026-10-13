import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import couple_photos_keyboard, result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_couple_photos_prompt
from bot.states import CouplePhotos


router = Router()
SECTION = "couple_photos"


@router.callback_query(F.data == "menu:couple_photos")
async def start_couple_photos(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(CouplePhotos.waiting_choice)
    await safe_answer_callback(callback)
    await callback.message.answer("📸 Что подготовить?", reply_markup=couple_photos_keyboard())


@router.callback_query(CouplePhotos.waiting_choice, F.data.startswith("couple_photos_choice:"))
async def choose_couple_photos(callback: CallbackQuery, state: FSMContext) -> None:
    choice = parse_callback_value(callback.data, "couple_photos_choice:")
    await state.update_data(choice=choice)
    await state.set_state(CouplePhotos.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "Опиши пару, стиль, место или настроение. Если описания нет — напиши «пропустить»."
    )


@router.message(CouplePhotos.waiting_description)
async def couple_photos_description(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    description = "" if (message.text or "").lower().strip() == "пропустить" else (message.text or "")
    await state.update_data(description=description)
    await _generate(message, message.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:couple_photos")
async def regenerate_couple_photos(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще идеи")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:couple_photos")
async def change_couple_photos(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CouplePhotos.waiting_choice)
    await safe_answer_callback(callback)
    await callback.message.answer("Выбери формат заново:", reply_markup=couple_photos_keyboard())


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    choice = data.get("choice")
    description = data.get("description", "")
    if not choice:
        await message.answer("Выбери, какие идеи фото нужны.")
        await state.set_state(CouplePhotos.waiting_choice)
        return

    text = await ai_service.generate_text(
        LOVEIS_SYSTEM_STYLE,
        build_couple_photos_prompt(choice, description),
        max_tokens=1300,
    )
    await state.set_state(CouplePhotos.done)
    await save_history(db, telegram_id, SECTION, {"choice": choice, "description": description}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

