from contextlib import suppress

import aiosqlite
from aiogram.types import CallbackQuery, Message

from bot.keyboards import currency_keyboard
from bot.repositories.user_repository import get_currency, upsert_user


async def ensure_currency(event: Message | CallbackQuery, db: aiosqlite.Connection) -> str | None:
    user = event.from_user
    await upsert_user(db, user)
    currency = await get_currency(db, user.id)
    if currency:
        return currency

    target = event.message if isinstance(event, CallbackQuery) else event
    await target.answer(
        "Сначала выбери валюту, чтобы я правильно считал бюджеты для свиданий, цветов и поездок.",
        reply_markup=currency_keyboard(),
    )
    if isinstance(event, CallbackQuery):
        await safe_answer_callback(event)
    return None


async def send_long_message(message: Message, text: str, reply_markup=None, limit: int = 3600) -> None:
    chunks = _split_text(text, limit)
    for chunk in chunks[:-1]:
        await message.answer(chunk)
    await message.answer(chunks[-1], reply_markup=reply_markup)


async def safe_answer_callback(callback: CallbackQuery, text: str | None = None) -> None:
    with suppress(Exception):
        await callback.answer(text)


def parse_callback_value(data: str, prefix: str) -> str:
    return data.removeprefix(prefix)


def parse_float(value: str) -> float | None:
    normalized = value.strip().lower().replace(",", ".")
    if normalized in {"пропустить", "по умолчанию", "default"}:
        return None
    try:
        number = float(normalized)
    except ValueError:
        return None
    return number if number > 0 else None


def _split_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in text.split("\n"):
        piece_len = len(paragraph) + 1
        if current and current_len + piece_len > limit:
            chunks.append("\n".join(current).strip())
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += piece_len

    if current:
        chunks.append("\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]

