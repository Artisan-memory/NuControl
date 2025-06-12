from __future__ import annotations
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from src.config import ADMIN_ID
from src.logging_setup import log_easy

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        message: Message = event
        user = message.from_user

        if not user:
            return await handler(event, data)

        # Check if userId == AdminID
        if user.id == ADMIN_ID:
            return await handler(event, data)

        # If not an admin
        log_easy(f'User @{user.username} tried to contact the bot')
        logger.info(f"Someone tried to contact bot | user_id: {user.id} | username: {user.username} | "
                    f"language_code: {user.language_code} | is_premium: {user.is_premium or False} | "
                    f"message: {message.text}")

        await message.reply('IT IS ME: <b>https://github.com/Artisan-memory/NuControl</b>')
        return None
