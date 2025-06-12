from aiogram import Router


def get_handlers_router() -> Router:
    from . import user_commands, bot_messages

    router = Router()
    router.include_router(user_commands.commands_router)
    router.include_router(bot_messages.router)

    return router
