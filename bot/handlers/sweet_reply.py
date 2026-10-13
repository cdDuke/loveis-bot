import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard, sweet_reply_style_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_sweet_reply_prompt
from bot.states import SweetReply


router = Router()
SECTION = "sweet_reply"


@router.callback_query(F.data == "menu:sweet_reply")
async def start_sweet_reply(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
) -> None:
    if not await ensure_currency(callback, db):
        return
    await state.set_state(SweetReply.waiting_message)
    await state.update_data(section=SECTION)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "💌 Пришли сообщение от девушки или парня, на которое хочешь красиво ответить."
    )


@router.message(SweetReply.waiting_message)
async def sweet_reply_message(message: Message, state: FSMContext) -> None:
    await state.update_data(message_text=message.text or "")
    await state.set_state(SweetReply.waiting_style)
    await message.answer("Выбери стиль ответа:", reply_markup=sweet_reply_style_keyboard())


@router.callback_query(SweetReply.waiting_style, F.data.startswith("sweet_style:"))
async def sweet_reply_style(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    style = parse_callback_value(callback.data, "sweet_style:")
    await state.update_data(style=style)
    await safe_answer_callback(callback, "Генерирую")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:sweet_reply")
async def regenerate_sweet_reply(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще варианты")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:sweet_reply")
async def change_sweet_reply(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SweetReply.waiting_message)
    await safe_answer_callback(callback)
    await callback.message.answer("Пришли новое сообщение, и я подберу ответ заново.")


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    message_text = data.get("message_text")
    style = data.get("style")
    if not message_text or not style:
        await message.answer("Мне нужно сообщение и стиль. Давай начнем заново.")
        await state.set_state(SweetReply.waiting_message)
        return

    prompt = build_sweet_reply_prompt(message_text, style)
    text = await ai_service.generate_text(LOVEIS_SYSTEM_STYLE, prompt)
    await state.set_state(SweetReply.done)
    await save_history(db, telegram_id, SECTION, {"message": message_text, "style": style}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

