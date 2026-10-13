import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard, situation_goal_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_situation_prompt
from bot.services.safety_service import check_relationship_safety
from bot.states import Situation


router = Router()
SECTION = "situation"


@router.callback_query(F.data == "menu:situation")
async def start_situation(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(Situation.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "🧠 Опиши ситуацию спокойно и как есть. Я помогу разобраться без давления и токсичных советов."
    )


@router.message(Situation.waiting_description)
async def situation_description(message: Message, state: FSMContext) -> None:
    description = message.text or ""
    safety = check_relationship_safety(description)
    await state.update_data(description=description, safety_level=safety.level, safety_message=safety.message)
    await state.set_state(Situation.waiting_goal)
    await message.answer("Чего ты хочешь сейчас?", reply_markup=situation_goal_keyboard())


@router.callback_query(Situation.waiting_goal, F.data.startswith("situation_goal:"))
async def situation_goal(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(goal=parse_callback_value(callback.data, "situation_goal:"))
    await safe_answer_callback(callback, "Разбираю ситуацию")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:situation")
async def regenerate_situation(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще вариант")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:situation")
async def change_situation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Situation.waiting_description)
    await safe_answer_callback(callback)
    await callback.message.answer("Опиши ситуацию заново.")


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    description = data.get("description")
    goal = data.get("goal")
    if not description or not goal:
        await message.answer("Нужно описание ситуации и цель.")
        await state.set_state(Situation.waiting_description)
        return

    safety_message = data.get("safety_message")
    generated = await ai_service.generate_text(
        LOVEIS_SYSTEM_STYLE,
        build_situation_prompt(description, goal, safety_message),
        max_tokens=1300,
    )

    if safety_message:
        text = f"⚠️ Важное про безопасность\n{safety_message}\n\n{generated}"
    else:
        text = generated

    await state.set_state(Situation.done)
    await save_history(db, telegram_id, SECTION, {"description": description, "goal": goal}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

