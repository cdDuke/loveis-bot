import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, safe_answer_callback, send_long_message
from bot.keyboards import diy_start_keyboard, result_keyboard
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_diy_prompt
from bot.services.budget_service import currency_symbol
from bot.states import Diy


router = Router()
SECTION = "diy"


@router.callback_query(F.data == "menu:diy")
async def start_diy(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    await state.set_state(Diy.waiting_details)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "🧸 Напиши условия: бюджет, время на подготовку, для неё/него и повод.\n"
        "Можно сразу нажать трендовую идею.",
        reply_markup=diy_start_keyboard(),
    )


@router.callback_query(F.data == "diy:trend")
async def trend_diy(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(
        details="Современная трендовая идея в стиле соцсетей, романтично, можно сделать за вечер.",
        trend=True,
    )
    await safe_answer_callback(callback, "Генерирую трендовую идею")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.message(Diy.waiting_details)
async def diy_details(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await state.update_data(details=message.text or "", trend=False)
    await _generate(message, message.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "regen:diy")
async def regenerate_diy(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    await safe_answer_callback(callback, "Еще идея")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service)


@router.callback_query(F.data == "change:diy")
async def change_diy(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Diy.waiting_details)
    await safe_answer_callback(callback)
    await callback.message.answer("Напиши новые условия или нажми трендовую идею.", reply_markup=diy_start_keyboard())


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
) -> None:
    data = await state.get_data()
    details = data.get("details", "")
    symbol = currency_symbol(data.get("currency"))
    trend = bool(data.get("trend"))
    text = await ai_service.generate_text(
        LOVEIS_SYSTEM_STYLE,
        build_diy_prompt(details, symbol, trend=trend),
        max_tokens=1300,
    )
    await state.set_state(Diy.done)
    await save_history(db, telegram_id, SECTION, {"details": details, "trend": trend}, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

