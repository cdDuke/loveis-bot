import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import compliments_style_keyboard, compliments_target_keyboard, result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_compliments_prompt
from bot.states import Compliments


router = Router()
SECTION = "compliments"


@router.callback_query(F.data == "menu:compliments")
async def start_compliments(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(Compliments.waiting_target)
    await safe_answer_callback(callback)
    await callback.message.answer("🥰 Для кого комплименты?", reply_markup=compliments_target_keyboard())


@router.callback_query(Compliments.waiting_target, F.data.startswith("compliments_target:"))
async def choose_compliments_target(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(target=parse_callback_value(callback.data, "compliments_target:"))
    await state.set_state(Compliments.waiting_style)
    await safe_answer_callback(callback)
    await callback.message.answer("Выбери стиль:", reply_markup=compliments_style_keyboard())


@router.callback_query(Compliments.waiting_style, F.data.startswith("compliments_style:"))
async def choose_compliments_style(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(style=parse_callback_value(callback.data, "compliments_style:"))
    await safe_answer_callback(callback, "Генерирую")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:compliments")
async def regenerate_compliments(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще комплименты")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:compliments")
async def change_compliments(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Compliments.waiting_target)
    await safe_answer_callback(callback)
    await callback.message.answer("Выбери заново, для кого комплименты:", reply_markup=compliments_target_keyboard())


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    target = data.get("target")
    style = data.get("style")
    if not target or not style:
        await message.answer("Нужно выбрать, для кого и в каком стиле.")
        await state.set_state(Compliments.waiting_target)
        return

    text = await ai_service.generate_text(
        LOVEIS_SYSTEM_STYLE,
        build_compliments_prompt(target, style),
        max_tokens=1000,
    )
    await state.set_state(Compliments.done)
    await save_history(db, telegram_id, SECTION, {"target": target, "style": style}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

