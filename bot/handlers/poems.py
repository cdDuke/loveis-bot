import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_poems_prompt
from bot.states import Poems


router = Router()
SECTION = "poems"


@router.callback_query(F.data == "menu:poems")
async def start_poems(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(Poems.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "📝 Опиши стих: для кого, повод, имена, настроение и длину. Можно коротко."
    )


@router.message(Poems.waiting_description)
async def poems_description(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(description=message.text or "")
    await _generate(message, message.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:poems")
async def regenerate_poems(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще стихи")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:poems")
async def change_poems(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Poems.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer("Опиши стих заново.")


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    description = (await state.get_data()).get("description")
    if not description:
        await message.answer("Напиши описание стиха.")
        await state.set_state(Poems.waiting_description)
        return

    text = await ai_service.generate_text(LOVEIS_SYSTEM_STYLE, build_poems_prompt(description), max_tokens=1200)
    await state.set_state(Poems.done)
    await save_history(db, telegram_id, SECTION, description, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

