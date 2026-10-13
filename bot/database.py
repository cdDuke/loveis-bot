from pathlib import Path

import aiosqlite


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    currency TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS request_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    section TEXT NOT NULL,
    user_input TEXT,
    bot_output TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


async def create_connection(database_path: Path) -> aiosqlite.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(database_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA foreign_keys=ON;")
    return db


async def init_db(database_path: Path) -> None:
    db = await create_connection(database_path)
    try:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    finally:
        await db.close()

