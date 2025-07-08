import asyncio
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger
from bot import bot, admins, dp, scheduler
from dao.middleware import DatabaseMiddlewareWithCommit, DatabaseMiddlewareWithOutCommit
from client import client
#from app.dao.database import async_session_maker 

#Дефолтное меню для всех пользователей
async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

#Функция которая выполнится когда бот запустится
async def start_bot():
    await set_commands()
    scheduler.start()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except:
            pass
    logger.info("Бот успешно запущен")

#Функция которая выполнится когда бот будет остановлен
async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Бот остановлен😔')
    except:
        pass
    logger.info("Бот остановлен!")

async def main():
    #Регистрация МИДЛВАРЕЙ
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithOutCommit())

    #Регистрация РОУТЕРОВ
    dp.include_router(client)
    # dp.include_router(user_router)
    # dp.include_router(admin_router)

    #Регистрация ФУНКЦИЙ
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    #Запуск бота в режиме long polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())