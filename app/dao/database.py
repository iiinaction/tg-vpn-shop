from datetime import datetime
from sqlalchemy import func, TIMESTAMP, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, declared_attr
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
# from config import database_url

def get_database_url():
    from config import database_url
    return database_url
url = get_database_url()

#Создание асинхронного движка для подключения к БД
engine = create_async_engine(url=url)
#Создание фабрики сессий
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)

#Базовый класс для моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True # Этот клас не будет использовать отдельную таблицу
    # metadata = DeclarativeBase.metadata
    #Общее поле "id" для всех таблиц
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    #Поля времени создания и обновления записи
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at:Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default= func.now(), onupdate = func.now()
    )

    #Автоматическое опредление имени таблицы
    # @declared_attr
    # def __tablename__(cls):
    #     return cls.__name__.lower() + 's'

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)