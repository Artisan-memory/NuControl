from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _
from loguru import logger

callbacks_router = Router(name="callbacks")


@callbacks_router.callback_query(F.data.startswith('task_kill_'))
async def callback_task_kill(call: CallbackQuery):
    from src.bot.callbacks.callbacks_func import task_kill
    task_name = call.data.removeprefix('task_kill_')

    text = await task_kill(task_name)

    await call.message.answer(text)
    await call.answer()


@callbacks_router.callback_query(F.data.startswith('ls_page_'))
async def callback_ls_page(call: CallbackQuery, bot: Bot):
    from src.bot.handlers.user_commands import render_listing
    page = int(call.data.removeprefix('ls_page_'))

    text, keyboard = await render_listing(bot, page)
    await call.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
    await call.answer()


@callbacks_router.callback_query(F.data == 'ls_noop')
async def callback_ls_noop(call: CallbackQuery):
    await call.answer()


@callbacks_router.callback_query(F.data.startswith('lang_'))
async def callback_language(call: CallbackQuery):
    from src.bot.callbacks.callbacks_func import set_language
    code = call.data.removeprefix('lang_')

    if not set_language(code):
        await call.answer()
        return

    logger.info(f"callback_language: language switched to {code}")
    # Локаль в этом апдейте уже зафиксирована мидлварью, так что берём новую вручную
    from src.bot.core.loader import i18n
    with i18n.use_locale(code):
        await call.message.edit_text(_("Language changed"))
    await call.answer()
