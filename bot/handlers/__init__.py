from aiogram import Dispatcher

from bot.handlers import (
    compliments,
    couple_photos,
    date,
    diy,
    flowers,
    menu,
    poems,
    settings,
    situation,
    start,
    sweet_reply,
    travel,
    videos,
    wish,
)


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(sweet_reply.router)
    dp.include_router(videos.router)
    dp.include_router(couple_photos.router)
    dp.include_router(date.router)
    dp.include_router(travel.router)
    dp.include_router(compliments.router)
    dp.include_router(situation.router)
    dp.include_router(wish.router)
    dp.include_router(diy.router)
    dp.include_router(flowers.router)
    dp.include_router(poems.router)
    dp.include_router(settings.router)
    dp.include_router(menu.router)

