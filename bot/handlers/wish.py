import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_wish_prompt
from bot.services.safety_service import check_relationship_safety
from bot.states import Wish


router = Router()
SECTION = "wish"


@router.callback_query(F.data == "menu:wish")
async def start_wish(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(Wish.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "🎁 Опиши условия желания. Например: «Она бросит курить, а я исполню желание, приятное нам обоим»."
    )


@router.message(Wish.waiting_description)
async def wish_description(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(description=message.text or "")
    await _generate(message, message.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:wish")
async def regenerate_wish(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще варианты")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:wish")
async def change_wish(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Wish.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer("Опиши условия заново.")


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    description = (await state.get_data()).get("description")
    if not description:
        await message.answer("Опиши условия желания.")
        await state.set_state(Wish.waiting_description)
        return

    safety = check_relationship_safety(description)
    if safety.level == "danger":
        text = safety.message or "В такой ситуации сначала подумай о безопасности."
    else:
        generated = await ai_service.generate_text(LOVEIS_SYSTEM_STYLE, build_wish_prompt(description), max_tokens=1200)
        text = f"{safety.message}\n\n{generated}" if safety.message else generated

    await state.set_state(Wish.done)
    await save_history(db, telegram_id, SECTION, description, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

