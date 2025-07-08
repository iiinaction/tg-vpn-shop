from typing import TypeVar, Generic, Any
from dao.database import Base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from loguru import logger
 
T = TypeVar("T", bound = Base)

class BaseDAO(Generic[T]):
    model: type[T]

    @classmethod
    async def find_one_or_none(cls, session:AsyncSession, filters:BaseModel):
        # найти одну запись по фильтрам
        filter_dict = filters.model_dump(exclude_unset=True)
        logger.info(f"Поиск по одной записи {cls.model.__name__} по фильтрам {filter_dict}")
        
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            if record:
                logger.info(f"Запись найдена по фильтрам {filter_dict}")
            else:
                logger.info(f"Запись не найдена по фильтрам{filter_dict}")
            return record
        
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиск записи по фильтрам {filter_dict}: {e}")
            raise