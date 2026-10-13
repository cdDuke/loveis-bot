import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, safe_answer_callback, send_long_message
from bot.keyboards import date_budget_keyboard, date_format_keyboard, result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_date_prompt
from bot.services.budget_service import currency_symbol, format_date_budget
from bot.states import DatePlan


router = Router()
SECTION = "date"


@router.callback_query(F.data == "menu:date")
async def start_date(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    symbol = currency_symbol(currency)
    await state.set_state(DatePlan.waiting_budget)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer("🌹 Выбери бюджет свидания:", reply_markup=date_budget_keyboard(symbol))


@router.callback_query(DatePlan.waiting_budget, F.data.startswith("date_budget:"))
async def choose_date_budget(callback: CallbackQuery, state: FSMContext) -> None:
    code = parse_callback_value(callback.data, "date_budget:")
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    if code == "custom":
        await state.update_data(budget_code=code)
        await state.set_state(DatePlan.waiting_custom_budget)
        await safe_answer_callback(callback)
        await callback.message.answer("Напиши свой бюджет числом или текстом, например: 5000.")
        return

    await state.update_data(budget_code=code, budget=format_date_budget(code, currency))
    await state.set_state(DatePlan.waiting_format)
    await safe_answer_callback(callback)
    await callback.message.answer("Выбери формат свидания:", reply_markup=date_format_keyboard())


@router.message(DatePlan.waiting_custom_budget)
async def custom_date_budget(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    budget = format_date_budget("custom", currency, message.text or "")
    await state.update_data(budget=budget)
    await state.set_state(DatePlan.waiting_format)
    await message.answer("Выбери формат свидания:", reply_markup=date_format_keyboard())


@router.callback_query(DatePlan.waiting_format, F.data.startswith("date_format:"))
async def choose_date_format(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(date_format=parse_callback_value(callback.data, "date_format:"))
    await safe_answer_callback(callback, "Готовлю план")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:date")
async def regenerate_date(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще вариант")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:date")
async def change_date(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    await state.set_state(DatePlan.waiting_budget)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "Выбери новый бюджет свидания:",
        reply_markup=date_budget_keyboard(currency_symbol(currency)),
    )


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    budget = data.get("budget")
    date_format = data.get("date_format")
    symbol = currency_symbol(data.get("currency"))
    if not budget or not date_format:
        await message.answer("Нужно выбрать бюджет и формат свидания.")
        await state.set_state(DatePlan.waiting_budget)
        return

    text = await ai_service.generate_text(
        LOVEIS_SYSTEM_STYLE,
        build_date_prompt(budget, date_format, symbol),
        max_tokens=1300,
    )
    await state.set_state(DatePlan.done)
    await save_history(db, telegram_id, SECTION, {"budget": budget, "format": date_format}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

