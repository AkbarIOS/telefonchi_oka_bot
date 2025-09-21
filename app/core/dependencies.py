from typing import AsyncGenerator
from fastapi import Depends
from app.core.config import settings
from app.repositories.database import DatabaseRepository
from app.services.telegram_service import TelegramService
from app.services.user_service import UserService
from app.services.advertisement_service import AdvertisementService
from app.handlers.bot_handler import BotHandler


# Database dependency
async def get_database() -> AsyncGenerator[DatabaseRepository, None]:
    db = DatabaseRepository(settings)
    await db.init_pool()
    try:
        yield db
    finally:
        await db.close_pool()


# Service dependencies
async def get_telegram_service() -> AsyncGenerator[TelegramService, None]:
    telegram_service = TelegramService(settings)
    try:
        yield telegram_service
    finally:
        await telegram_service.close()


async def get_user_service(
    db: DatabaseRepository = Depends(get_database),
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> UserService:
    return UserService(db, telegram_service)


async def get_advertisement_service(
    db: DatabaseRepository = Depends(get_database),
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> AdvertisementService:
    return AdvertisementService(db, telegram_service, settings)


async def get_bot_handler(
    user_service: UserService = Depends(get_user_service),
    advertisement_service: AdvertisementService = Depends(get_advertisement_service),
    telegram_service: TelegramService = Depends(get_telegram_service)
) -> BotHandler:
    return BotHandler(user_service, advertisement_service, telegram_service)