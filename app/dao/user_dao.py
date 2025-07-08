from sqlalchemy.orm import selectinload
from models import User, VPNCategory, VPN, UserVPN
from sqlalchemy import select, update, delete, desc, join, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import datetime
from typing import Optional, List, Dict
from dao.base import BaseDAO

class UserDAO(BaseDAO[User]):
    model = User
    #Создание триала для клиента

    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_user(self, telegram_id: int, name:str)->User:
            user = select(User).where(User.telegram_id==telegram_id)
            result = await self.session.execute(user)
            user = result.scalar_one_or_none()

            if not user:
                days_later = datetime.datetime.now() + datetime.timedelta(days=7)
                user = User(
                    telegram_id = telegram_id,
                    username =  name, 
                    trial_until =days_later)
                self.session.add(user)
                await self.session.commit()

            return user
    
    @classmethod
    async def get_purchase_statistic(cls, session:AsyncSession, telegram_id: int) -> Optional[Dict[str, int]]:
         try:
              #Запрос для получения общего числа покупок и общей суммы
              result = await session.execute(
                   select(
                        func.count(VPN.id).label("total_purchases"),
                        func.sum(VPN.price).label("total_amount")
                   )
                   .select_from(User)
                   .join(UserVPN, UserVPN.user_id == User.id)
                   .join(VPN, VPN.id == UserVPN.vpn_id)
                   .filter(User.telegram_id==telegram_id)
              )
              stats = result.one_or_none()

              if stats is None:
                   return None
              total_purchases, total_amount = stats
              
              return {
                   'total_purchases' : total_purchases,
                   'total_amount' : total_amount or 0
              }
         
         except SQLAlchemyError as e:
              #Обработка ошибок при работе с бд
              print(f'Ошибка получения статистики {e}')
              return None
         




    # Показать пользователей
    async def get_all_users(self) -> list[User]:
            result = await self.session.scalars(select(User))
            users = result.all()
            return users

    #Показать категории
    async def get_vpn_categories(self):
            result = self.session.scalar(select(VPNCategory))
            categories = result.all()
            return categories


    async def get_countries(self, vpn_category_id, user):
        """
        Получить список VPN-серверов для заданной категории,
        которые доступны для подключения.

        Args:
            vpn_category_id (int): ID категории VPN.
            user (User): Объект пользователя (пока не используется).

        Returns:
            List[VPN]: Список объектов VPN, отсортированных по цене (убывание).

        TODO:
            - В будущем использовать параметр `user` для фильтрации серверов
            по региону, подписке или другим правам доступа пользователя.
            - Добавить кэширование результатов для оптимизации.
        """

        result = self.session.scalars(
                select(VPN).where(and_(
                    VPN.category_id == vpn_category_id,
                    VPN.price > 0,
                    VPN.current_conn < VPN.max_conn
                )).order_by(VPN.price.desc())
            )
        countries = result.all()
        return countries


    # Выбрать VPN по id
    async def get_vpn(self, vpn_id):
         return self.session.scalar(select(VPN).where(VPN.id == vpn_id))
    

    #Добавить бесплатный VPN
    async def add_user_free_vpn(self, user, vpn_id):
            self.session.add(UserVPN(user_id=user.id, vpn_id=vpn_id, until=user.trial_until))
            vpn = await self.session.scalar(select(VPN).where(VPN.id == vpn_id))
            if vpn is None:
                raise ValueError(f"VPN с id={vpn_id} не найден!")
            vpn.current_conn += 1
            await self.session.commit()

    #Добавить пользователю VPN
    async def add_user_vpn(self, user, vpn_id, days):
        """
        Назначает пользователю VPN на указанное число дней и увеличивает счётчик подключений.
        """
        days_until = datetime.datetime.now() + datetime.timedelta(days=days)
        self.session.add(UserVPN(user_id = user.id, vpn_id = vpn_id, until = days_until))
        vpn = await self.session.scalar(select(VPN).where(VPN.id == vpn_id))
        if vpn is None:
            raise ValueError(f"VPN c id:{vpn_id} не найден!")
        vpn.current_conn += 1
        await self.session.commit()

    #Обновить статус VPN у пользователя
    async def delete_user_vpn(self, tg_id: int, vpn_id: int) -> None:
        """
        Помечает VPN как отключённый для пользователя и уменьшает счётчик подключений.

        Args:
            tg_id (int): Telegram ID пользователя.
            vpn_id (int): ID VPN сервера.

        Raises:
            ValueError: Если пользователь или VPN не найдены.
        """
        user = await self.session.scalar(select(User).where(User.tg_id == tg_id))
        if user is None:
            raise ValueError(f'User с id{tg_id} не найден!')
        vpn = await self.session.scalar(select(VPN).where(VPN.id == vpn_id))
        if vpn is None:
            raise ValueError(f'VPN с id:{tg_id} не найден!')
        await self.session.execute(
            update(UserVPN).where(
                and_(
                    UserVPN.user_id == user.id, 
                    UserVPN.vpn_id == vpn_id
                )
            ).values(status=False)
            )
        vpn.current_conn = max(0, vpn.current_conn - 1)
        await self.session.commit()

    async def get_user_vpn(self, user, vpn_id):
        """Возвращает объект UserVPN для конкретного пользователя и VPN, если он существует."""
        
        return await self.session.scalar(
            select(UserVPN).where(
                and_(
                    UserVPN.user_id == user.id, 
                    UserVPN.vpn_id ==vpn_id
                )
            )
            )

    async def get_sendall_users(self, client_type:str) -> list[int]:
        """
    Возвращает список tg_id пользователей:
    - если client_type == 'free' — у которых нет платных VPN;
    - если client_type == 'paid' — у которых есть хотя бы один платный VPN.
        """
        result = await self.session.execute(
            select(User).options(
                selectinload(User.vpns).selectinload(UserVPN.vpn)
            )
        )
        users = result.scalars().all()
        tg_ids = []

        for user in users:
            has_paid = any(user_vpn.vpn.price > 0 for user_vpn in user.vpns)
        if client_type == 'free' and not has_paid:
            tg_ids.append(user.tg_id)
        elif client_type == 'paid' and has_paid:
            tg_ids.append(user.tg_id)
        return tg_ids
        
    # async with async_session_maker() as session:
    #     users_list = list()
    #     users = await session.execute(
    #         select(User).options(selectinload(User.vpns).selectinload(UserVPN.vpn)
    #                              )
    #     )
    #     users = users.scalars().all()
    #     flag = False

    #     if client_type == 'free':
    #         for user in users:
    #             for user_vpn in user.vpns:
    #                 if user_vpn.vpn.price > 0:
    #                     flag = True
    #                     break

    #             if flag:
    #                 continue
    #             users_list.append(user.tg_id)
    #     elif client_type == 'paid':
    #         for user in users:
    #             for user_vpn in user.vpns:
    #                 if user_vpn.vpn.price > 0:
    #                     flag = True
    #             if not flag:
    #                 continue
    #             users_list.append(user.tg_id)
    #     return users_list