from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, Text, ForeignKey, Integer, String, Boolean
from dao.database import Base
from sqlalchemy import DateTime
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str|None] = mapped_column(String(32), nullable=True) 
    first_name: Mapped[str|None] = mapped_column(String(32), nullable=True)
    last_name:Mapped[str|None] = mapped_column(String(32), nullable=True)
    trial_until:Mapped[datetime] = mapped_column(DateTime)

    #Отношения к VPN подключениям
    vpns: Mapped[list['UserVPN']] = relationship(back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

class VPNCategory(Base):
    __tablename__ = 'vpn_categories'

    name: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)

    #Отношение к VPN-серверам
    vpns: Mapped[list['VPN']] = relationship(back_populates='category')

    #VPN сервер
class VPN(Base):
    __tablename__ = 'vpns'
    
    name: Mapped[str] = mapped_column(String(125), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    max_conn: Mapped[int] = mapped_column(Integer, nullable=False)
    current_conn: Mapped[int] = mapped_column(Integer, nullable=False)
    server_ip: Mapped[str] = mapped_column(String(125), nullable=False)
    server_hash: Mapped[str] = mapped_column(String(125), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('vpn_categories.id'))
    category: Mapped['VPNCategory'] = relationship(back_populates='vpns')
    users: Mapped[list['UserVPN']] = relationship(back_populates='vpn')

class UserVPN(Base):
    __tablename__ = 'user_vpn'

    user_id:Mapped[int] = mapped_column(Integer, ForeignKey('users.id')) 
    vpn_id:Mapped[int] = mapped_column(Integer, ForeignKey('vpns.id'))
    until:Mapped[datetime] = mapped_column(DateTime)
    status:Mapped[bool] = mapped_column(Boolean, default=True)

    #Отношения
    user: Mapped['User'] = relationship(back_populates='vpns')
    vpn: Mapped['VPN'] = relationship(back_populates='users')

