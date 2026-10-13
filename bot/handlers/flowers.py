import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, safe_answer_callback, send_long_message
from bot.keyboards import result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_flowers_prompt
from bot.services.budget_service import currency_symbol
from bot.services.flower_service import flower_budget_guidance
from bot.states import Flowers


router = Router()
SECTION = "flowers"


@router.callback_query(F.data == "menu:flowers")
async def start_flowers(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    await state.set_state(Flowers.waiting_recipient)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer("💐 Для кого букет?")


@router.message(Flowers.waiting_recipient)
async def flowers_recipient(message: Message, state: FSMContext) -> None:
    await state.update_data(recipient=message.text or "")
    await state.set_state(Flowers.waiting_loved_flowers)
    await message.answer("Какие цветы любит человек? Если не знаешь — так и напиши.")


@router.message(Flowers.waiting_loved_flowers)
async def flowers_loved(message: Message, state: FSMContext) -> None:
    await state.update_data(loved_flowers=message.text or "")
    await state.set_state(Flowers.waiting_colors)
    await message.answer("Какие цвета нравятся?")


@router.message(Flowers.waiting_colors)
async def flowers_colors(message: Message, state: FSMContext) -> None:
    await state.update_data(colors=message.text or "")
    await state.set_state(Flowers.waiting_reason)
    await message.answer("Какой повод?")


@router.message(Flowers.waiting_reason)
async def flowers_reason(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    symbol = currency_symbol(data.get("currency"))
    await state.update_data(reason=message.text or "")
    await state.set_state(Flowers.waiting_budget)
    await message.answer(f"Какой бюджет? Напиши примерно в {symbol}.")


@router.message(Flowers.waiting_budget)
async def flowers_budget(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(budget=message.text or "")
    await _generate(message, message.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:flowers")
async def regenerate_flowers(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще букет")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:flowers")
async def change_flowers(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Flowers.waiting_recipient)
    await safe_answer_callback(callback)
    await callback.message.answer("Начнем заново. Для кого букет?")


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    required = ("recipient", "loved_flowers", "colors", "reason", "budget")
    if any(not data.get(key) for key in required):
        await message.answer("Нужно ответить на все вопросы про букет.")
        await state.set_state(Flowers.waiting_recipient)
        return

    currency = data.get("currency", "RUB")
    symbol = currency_symbol(currency)
    guidance = flower_budget_guidance(currency, data["budget"])
    prompt = build_flowers_prompt(
        data["recipient"],
        data["loved_flowers"],
        data["colors"],
        data["reason"],
        data["budget"],
        symbol,
        guidance,
    )
    text = await ai_service.generate_text(LOVEIS_SYSTEM_STYLE, prompt, max_tokens=1300)
    await state.set_state(Flowers.done)
    await save_history(db, telegram_id, SECTION, data, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

