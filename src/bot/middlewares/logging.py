from __future__ import annotations
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from loguru import logger

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineQuery, Message, PreCheckoutQuery, Update


class LoggingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.logger = logger
        super().__init__()

    def process_message(self, message: Message) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {"chat_type": message.chat.type}

        if message.from_user:
            print_attrs["user_id"] = message.from_user.id
        if message.text:
            print_attrs["text"] = message.text
        if message.video:
            print_attrs["caption"] = message.caption
            print_attrs["caption_entities"] = message.caption_entities
            print_attrs["video_id"] = message.video.file_id
            print_attrs["video_unique_id"] = message.video.file_unique_id
        if message.audio:
            print_attrs["duration"] = message.audio.duration
            print_attrs["file_size"] = message.audio.file_size
        if message.photo:
            print_attrs["caption"] = message.caption
            print_attrs["caption_entities"] = message.caption_entities
            print_attrs["photo_id"] = message.photo[-1].file_id
            print_attrs["photo_unique_id"] = message.photo[-1].file_unique_id

        return print_attrs

    def process_callback_query(self, callback_query: CallbackQuery) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {
            "query_id": callback_query.id,
            "data": callback_query.data,
            "user_id": callback_query.from_user.id,
            "inline_message_id": callback_query.inline_message_id,
        }

        if callback_query.message:
            print_attrs["message_id"] = callback_query.message.message_id
            print_attrs["chat_type"] = callback_query.message.chat.type
            print_attrs["chat_id"] = callback_query.message.chat.id

        return print_attrs

    def process_inline_query(self, inline_query: InlineQuery) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {
            "query_id": inline_query.id,
            "user_id": inline_query.from_user.id,
            "query": inline_query.query,
            "offset": inline_query.offset,
            "chat_type": inline_query.chat_type,
            "location": inline_query.location,
        }

        return print_attrs

    def process_pre_checkout_query(self, pre_checkout_query: PreCheckoutQuery) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {
            "query_id": pre_checkout_query.id,
            "user_id": pre_checkout_query.from_user.id,
            "currency": pre_checkout_query.currency,
            "amount": pre_checkout_query.total_amount,
            "payload": pre_checkout_query.invoice_payload,
            "option": pre_checkout_query.shipping_option_id,
        }

        return print_attrs

    def process_my_chat_member(self, my_chat_member: ChatMemberUpdated) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {
            "user_id": my_chat_member.from_user.id,
            "chat_id": my_chat_member.chat.id,
        }

        return print_attrs

    def process_chat_member(self, chat_member: ChatMemberUpdated) -> dict[str, Any]:
        print_attrs: dict[str, Any] = {
            "user_id": chat_member.from_user.id,
            "chat_id": chat_member.chat.id,
            "old_state": chat_member.old_chat_member,
            "new_state": chat_member.new_chat_member,
        }

        return print_attrs

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        sources = [
            (event.message, self.process_message, "received message"),
            (event.callback_query, self.process_callback_query, "received callback query"),
            (event.inline_query, self.process_inline_query, "received inline query"),
            (event.pre_checkout_query, self.process_pre_checkout_query, "received pre-checkout query"),
            (event.my_chat_member, self.process_my_chat_member, "received my chat member update"),
            (event.chat_member, self.process_chat_member, "received chat member update"),
        ]

        for obj, process, label in sources:
            if obj is not None:
                attrs = process(obj)
                details = " | ".join(f"{key}: {value}" for key, value in attrs.items() if value is not None)
                self.logger.info(f"{label} | {details}")
                break

        return await handler(event, data)
