from typing import Any

import aiosqlite
from aiogram.types import User


async def upsert_user(db: aiosqlite.Connection, user: User, currency: str | None = None) -> None:
    existing = await get_user(db, user.id)
    username = user.username
    first_name = user.first_name

    if existing:
        if currency is None:
            await db.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
                """,
                (username, first_name, user.id),
            )
        else:
            await set_currency(db, user.id, currency, commit=False)
            await db.execute(
                """
                UPDATE users
                SET username = ?, first_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
                """,
                (username, first_name, user.id),
            )
    else:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, currency)
            VALUES (?, ?, ?, ?)
            """,
            (user.id, username, first_name, currency),
        )
    await db.commit()


async def get_user(db: aiosqlite.Connection, telegram_id: int) -> aiosqlite.Row | None:
    cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    return await cursor.fetchone()


async def get_currency(db: aiosqlite.Connection, telegram_id: int) -> str | None:
    user = await get_user(db, telegram_id)
    if not user:
        return None
    return user["currency"]


async def set_currency(
    db: aiosqlite.Connection,
    telegram_id: int,
    currency: str,
    *,
    commit: bool = True,
) -> None:
    await db.execute(
        """
        UPDATE users
        SET currency = ?, updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (currency, telegram_id),
    )
    if commit:
        await db.commit()


async def save_history(
    db: aiosqlite.Connection,
    telegram_id: int,
    section: str,
    user_input: Any,
    bot_output: str,
) -> None:
    await db.execute(
        """
        INSERT INTO request_history (telegram_id, section, user_input, bot_output)
        VALUES (?, ?, ?, ?)
        """,
        (
            telegram_id,
            section,
            _shorten(str(user_input), 1200),
            _shorten(bot_output, 2500),
        ),
    )
    await db.commit()


async def clear_history(db: aiosqlite.Connection, telegram_id: int) -> None:
    await db.execute("DELETE FROM request_history WHERE telegram_id = ?", (telegram_id,))
    await db.commit()


def _shorten(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1] + "…"

