from aiogram import Router, F
from aiogram.types import CallbackQuery

callbacks_router = Router(name="callbacks")

@callbacks_router.callback_query(F.data.startswith(('task_kill_')))
async def callback_task_kill(call: CallbackQuery):
    from src.bot.callbacks.callbacks_func import task_kill
    task_name = call.data.split('_')[2]

    text = await task_kill(task_name)

    await call.message.answer(text)
    await call.answer()
