from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from dao.database import async_session_maker
from dao.user_dao import UserDAO
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
from models import User

class BaseDatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message |CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, any]
    ) -> Any:
        async with async_session_maker() as session:           #Устанавливаем сессию
            self.set_session(data, session)
            try:
                result = await handler(event, data)
                await self.after_handler(session)
                return result
            
            except Exception as e:
                await session.rollback()
                raise e
            
            finally:
                await session.close()
    def set_session(self, data:Dict[str, Any], session) -> None:
        raise NotImplementedError("Этот метод должен быть реализован в подклассах.")
    
    async def after_handler(self, session) -> None:
        """Метод для выполнения действия после обработки события. По умолчанию ничего не делает"""
        pass

class DatabaseMiddlewareWithOutCommit(BaseDatabaseMiddleware):
    def set_session(self, data: Dict[str, Any], session) -> None:
        """Устанавливаем сессию без коммита"""
        data['session_without_commit'] = session

class DatabaseMiddlewareWithCommit(BaseDatabaseMiddleware):
    def set_session(self, data:Dict[str, Any], session) -> None:
        """Устанавливаем сессию с коммитом"""
        data['session_with_commit'] = session
    
    async def after_handler(self, session) -> None:
        """Фиксируем изменения после обработки события"""
        await session.commit()




# class UserMiddleware(BaseMiddleware):
#     def __init__(self, sessionmaker: async_sessionmaker):
#         super().__init__()
#         self.sessionmaker = sessionmaker
    
#     async def __call__(
#             self,
#             handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
#             event: TelegramObject,
#             data: Dict[str, Any]
#     ) -> Any:
#         if not hasattr(event, 'from_user') or event.from_user is None:
#             return await handler(event, data)
        
#         async with self.sessionmaker() as session:
#             dao = UserDAO(session)
#             user: User = await dao.set_user(
#                 telegram_id = event.from_user.id,
#                 name=event.from_user.full_name,
#             )
#             data['user'] = user
        
#         return await handler(event, data)