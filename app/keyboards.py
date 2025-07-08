from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import settings
import requests as db
import datetime

#Главное меню клиента

def client_main_kb(user_id:int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🌍Купить VPN', callback_data='buy')
    kb.button(text='👤Профиль', callback_data='my_profile')
    kb.button(text='👨‍💻Тех.Поддержка', callback_data='support')
    kb.button(text='💌О нас', callback_data='info')
    if user_id in settings.ADMIN_IDS:
        kb.button(text='⚙️Админ панель', callback_data='admin_panel')
    kb.adjust(1)
    return kb.as_markup()

def purchases_kb(product_id, price) ->InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='🗑Посмотреть мои ключи', callback_data='purchases')
    kb.button(text='🏠На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def product_kb(product_id, price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text='💸Купить', callback_data=f'buy_{product_id}_price{price}')
    kb.button(text='🛍Назад', callback_data='catalog')
    kb.button(text='🏠 На главную', callback_data='home')
    kb.adjust(1)
    return kb.as_markup()

def get_product_buy_kb(price) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'Оплатить{price}₽', pay=True)],
        [InlineKeyboardButton(text='Отменить', callback_data='home')]
    ])

def go_on_main() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑 Смотреть покупки", callback_data="purchases")
    kb.button(text="🏠 На главную", callback_data="my_profile")
    kb.adjust(1)
    return kb.as_markup()

async def sendall_choose_client():
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=f'Всем пользователям', callback_data=f'sendall_all'))
    kb.add(InlineKeyboardButton(text=f'Клиентам с бесплатными серверами', callback_data=f'sendall_free'))
    kb.add(InlineKeyboardButton(text=f'Клиентам с платными серверами', callback_data=f'sendall_paid'))
    kb.add(InlineKeyboardBuilder(text=f'Отмена', callback_data=f'start'))
    return kb.adjust(1).as_markup()
