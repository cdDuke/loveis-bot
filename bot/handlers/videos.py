import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard, videos_target_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_videos_prompt
from bot.states import Videos


router = Router()
SECTION = "videos"


@router.callback_query(F.data == "menu:videos")
async def start_videos(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(Videos.waiting_target)
    await safe_answer_callback(callback)
    await callback.message.answer("🎬 Для кого делаем идею видео?", reply_markup=videos_target_keyboard())


@router.callback_query(Videos.waiting_target, F.data.startswith("videos_target:"))
async def choose_videos_target(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    target = parse_callback_value(callback.data, "videos_target:")
    await state.update_data(target=target)
    await safe_answer_callback(callback, "Генерирую идеи")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:videos")
async def regenerate_videos(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще идеи")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:videos")
async def change_videos(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Videos.waiting_target)
    await safe_answer_callback(callback)
    await callback.message.answer("Выбери, для кого подготовить видео:", reply_markup=videos_target_keyboard())


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    target = (await state.get_data()).get("target")
    if not target:
        await message.answer("Выбери, для кого делаем видео.")
        await state.set_state(Videos.waiting_target)
        return

    text = await ai_service.generate_text(LOVEIS_SYSTEM_STYLE, build_videos_prompt(target), max_tokens=1500)
    await state.set_state(Videos.done)
    await save_history(db, telegram_id, SECTION, target, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

