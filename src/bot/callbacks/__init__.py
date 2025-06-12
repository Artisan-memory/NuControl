from aiogram import Router

def get_callbacks_router() -> Router:
    from . import callbacks

    router = Router()
    router.include_router(callbacks.callbacks_router)

    return router
