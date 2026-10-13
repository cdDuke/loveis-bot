import aiosqlite
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.handlers.helpers import ensure_currency, parse_callback_value, parse_float, safe_answer_callback, send_long_message
from bot.keyboards import (
    car_consumption_keyboard,
    fuel_price_keyboard,
    result_keyboard,
    travel_transport_keyboard,
    travel_type_keyboard,
)
from bot.repositories.user_repository import save_history
from bot.services.ai_service import AIService, LOVEIS_SYSTEM_STYLE, build_travel_romance_prompt
from bot.services.budget_service import currency_symbol, default_fuel_price
from bot.services.travel_service import MockTravelProvider, TravelInput, format_trip_estimate
from bot.states import Travel


router = Router()
SECTION = "travel"


@router.callback_query(F.data == "menu:travel")
async def start_travel(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    await state.set_state(Travel.waiting_destination_type)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer("✈️ Что хочешь указать?", reply_markup=travel_type_keyboard())


@router.callback_query(Travel.waiting_destination_type, F.data.startswith("travel_type:"))
async def choose_destination_type(callback: CallbackQuery, state: FSMContext) -> None:
    destination_type = parse_callback_value(callback.data, "travel_type:")
    await state.update_data(destination_type=destination_type)
    await state.set_state(Travel.waiting_destination)
    await safe_answer_callback(callback)
    await callback.message.answer(f"Напиши {destination_type.lower()}, куда хотите поехать.")


@router.message(Travel.waiting_destination)
async def enter_destination(message: Message, state: FSMContext) -> None:
    await state.update_data(destination=(message.text or "").strip())
    await state.set_state(Travel.waiting_transport)
    await message.answer("Выбери транспорт:", reply_markup=travel_transport_keyboard())


@router.callback_query(Travel.waiting_transport, F.data.startswith("travel_transport:"))
async def choose_transport(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
    travel_provider: MockTravelProvider,
) -> None:
    transport = parse_callback_value(callback.data, "travel_transport:")
    await state.update_data(transport=transport)
    await safe_answer_callback(callback)

    if transport == "Машина":
        await state.set_state(Travel.waiting_car_consumption)
        await callback.message.answer(
            "Напиши расход топлива на 100 км. Если не знаешь — используй дефолт.",
            reply_markup=car_consumption_keyboard(),
        )
        return

    await _generate(callback.message, callback.from_user.id, state, db, ai_service, travel_provider)


@router.callback_query(Travel.waiting_car_consumption, F.data == "travel_car:consumption_default")
async def default_consumption(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(fuel_consumption=8.0)
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    await state.set_state(Travel.waiting_car_fuel_price)
    await safe_answer_callback(callback)
    await callback.message.answer(
        "Теперь укажи цену бензина за литр или используй дефолт.",
        reply_markup=fuel_price_keyboard(default_fuel_price(currency), currency_symbol(currency)),
    )


@router.message(Travel.waiting_car_consumption)
async def enter_consumption(message: Message, state: FSMContext) -> None:
    value = parse_float(message.text or "")
    if value is None:
        await message.answer(
            "Напиши число, например 8.5, или нажми кнопку дефолта.",
            reply_markup=car_consumption_keyboard(),
        )
        return

    await state.update_data(fuel_consumption=value)
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    await state.set_state(Travel.waiting_car_fuel_price)
    await message.answer(
        "Теперь укажи цену бензина за литр или используй дефолт.",
        reply_markup=fuel_price_keyboard(default_fuel_price(currency), currency_symbol(currency)),
    )


@router.callback_query(Travel.waiting_car_fuel_price, F.data == "travel_car:fuel_default")
async def default_fuel(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
    travel_provider: MockTravelProvider,
) -> None:
    data = await state.get_data()
    currency = data.get("currency", "RUB")
    await state.update_data(fuel_price=float(default_fuel_price(currency)))
    await safe_answer_callback(callback, "Считаю")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service, travel_provider)


@router.message(Travel.waiting_car_fuel_price)
async def enter_fuel(
    message: Message,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
    travel_provider: MockTravelProvider,
) -> None:
    value = parse_float(message.text or "")
    if value is None:
        data = await state.get_data()
        currency = data.get("currency", "RUB")
        await message.answer(
            "Напиши цену числом, например 65, или используй дефолт.",
            reply_markup=fuel_price_keyboard(default_fuel_price(currency), currency_symbol(currency)),
        )
        return

    await state.update_data(fuel_price=value)
    await _generate(message, message.from_user.id, state, db, ai_service, travel_provider)


@router.callback_query(F.data == "regen:travel")
async def regenerate_travel(
    callback: CallbackQuery,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
    travel_provider: MockTravelProvider,
) -> None:
    await safe_answer_callback(callback, "Пересчитываю")
    await _generate(callback.message, callback.from_user.id, state, db, ai_service, travel_provider)


@router.callback_query(F.data == "change:travel")
async def change_travel(callback: CallbackQuery, state: FSMContext, db: aiosqlite.Connection) -> None:
    currency = await ensure_currency(callback, db)
    if not currency:
        return
    await state.set_state(Travel.waiting_destination_type)
    await state.update_data(currency=currency)
    await safe_answer_callback(callback)
    await callback.message.answer("Что хочешь указать?", reply_markup=travel_type_keyboard())


async def _generate(
    message: Message,
    telegram_id: int,
    state: FSMContext,
    db: aiosqlite.Connection,
    ai_service: AIService,
    travel_provider: MockTravelProvider,
) -> None:
    data = await state.get_data()
    required = ("destination_type", "destination", "transport", "currency")
    if any(not data.get(key) for key in required):
        await message.answer("Нужно выбрать направление и транспорт. Давай начнем заново.")
        await state.set_state(Travel.waiting_destination_type)
        return

    trip = TravelInput(
        destination_type=data["destination_type"],
        destination=data["destination"],
        transport=data["transport"],
        currency=data["currency"],
        fuel_consumption=data.get("fuel_consumption"),
        fuel_price=data.get("fuel_price"),
    )
    estimate = await travel_provider.estimate_trip(trip)
    base_text = format_trip_estimate(estimate)

    if ai_service.enabled:
        romance = await ai_service.generate_text(
            LOVEIS_SYSTEM_STYLE,
            build_travel_romance_prompt(base_text),
            max_tokens=700,
        )
        text = f"{base_text}\n\n💕 Как сделать поездку теплее\n{romance}"
    else:
        text = base_text

    await state.set_state(Travel.done)
    await save_history(db, telegram_id, SECTION, data, text)
    await send_long_message(message, text, reply_markup=result_keyboard(SECTION))

