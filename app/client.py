import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
import dao.user_dao as db
import states as st
import keyboards as kb
from dao.middleware import BaseDatabaseMiddleware
from datetime import datetime, timedelta, timezone
from bot import scheduler
from outline_api import create_access_key, rename_access_key
from apsched import send_message
from dao.user_dao import User, UserDAO, UserVPN
from dao.schemas import TelegramIDModel
from bot import bot
from config import settings

#Работа с middlewares
client = Router()

#Авторизация пользователя
@client.message(CommandStart())
async def send_main_menu(message:Message, session_with_commit:AsyncSession, state:FSMContext):
    user_id = message.from_user.id
    user_info = await UserDAO.find_one_or_none(
        session = session_with_commit,
        filters = TelegramIDModel(telegram_id = user_id)
    )
    if user_info.trial_until > datetime.now():
        if user_info.trial_until > datetime.now():
            await message.answer(
                text = f'🤖<b>Добро пожаловать</b> \n\n🆓Ваш пробный период действует еще {user_info.trial_until}',
                reply_markup=kb.client_main_kb
                )
    else:
        await message.answer(
                text=f'🤖<b>Добро пожаловать</b> \n\nПриобретайте безопасный,устойчивый высокоскоростной VPN у нас!',
                reply_markup=kb.client_main_kb(user_info.telegram_id)
            )
        await state.clear()

@client.callback_query(F.data == 'my_profile')
async def page_about(call:CallbackQuery, session_without_commit:AsyncSession):
    await call.answer("Профиль")
    #Получаем статистику пользователя
    purchases = await UserDAO.get_purchase_statistic(session=session_without_commit, telegram_id=call.from_user.id)
    print(f'количество покупок {purchases}')
    if purchases is None:
        total_amount = 0
        total_purchases = 0
    else:
        total_amount = purchases.get("total_amount", 0)
        total_purchases = purchases.get("total_purchases", 0)
    #формируем сообщение в зависимости от наличия покупок
    if total_purchases ==0:
        await call.message.answer(
            text = "🔍 <b>У вас пока нет покупок.</b>\n\n"
                 "Откройте каталог и выберите что-нибудь интересное!",
            reply_markup=kb.client_main_kb(call.from_user.id)
        )
    else:
        text = (f"🛍 <b>Ваш профиль:</b>\n\n"
            f"Количество покупок: <b>{total_purchases}</b>\n"
            "Хотите просмотреть детали ваших покупок?"
            )
        await call.message.answer(
            text=text,
            reply_markup=kb.go_on_main()
        )



@client.callback_query(F.data.startswith('category_'))
async def choose_country(callback:CallbackQuery, user:User):
    await callback.answer('Выбор региона')
    vpn_category_id = callback.data.split('_'[1])
    await callback.message.edit_text(f'🏳️<b>Выберите регион</b> \n\n Советуем выбирать регион поближе к вам для меньшей задержки',
                                     reply_markup=await kb.get_countries(vpn_category_id, user))





@client.callback_query(F.data=='back_to_choose_category')
async def choose_vpn_category(event: Message | CallbackQuery):
    if isinstance(event, Message):
        await event.answer('🌎<b>Выбор протокола</b> \n\n Outline - ?')

    elif isinstance(event, CallbackQuery):
        await event.answer('Выбор протокола')
        await event.message.edit_text('🌎<b>Выбор протокола</b> \n\n Outline - ?')


#Функция покупки
@client.callback_query(F.data.startswith('buy_'))
async def process_about(call:CallbackQuery, session_without_commit:AsyncSession):
    user_info = await UserDAO.find_one_or_none(
        session=session_without_commit,
        filters=TelegramIDModel(telegram_id=call.from_user.id)
    )
    _, product_id, price = call.data.split('_')
    await bot.send_invoice(
        chat_id = call.from_user.id,
        title=f'Оплата 👉 {price}₽',
        description=f'Пожалуйста, завершите оплату в размере {price}₽, чтобы получить свой VPN ключ.',
        payload = f'{user_info.id}_{product_id}',
        provider_token=settings.PROVIDER_TOKEN,
        currency='rub',
        prices=[LabeledPrice(
            label=f'Оплата {price}',
            amount = int(price) * 100
        )],
        reply_markup= get_product_buy_kb(price)
    ) 
    await call.message.delete()









    
@client.callback_query(F.data.startswith('country_'))
async def create_connection(callback:CallbackQuery, user:User, bot:Bot, state:FSMContext):
    vpn_id = callback.data.split('_')[1]
    vpn = await db.get_vpn(vpn_id)
    is_vpn = await db.get_user_vpn(user, vpn)
    if is_vpn:
        await callback.answer('Подписка на данный VPN раннее была оформлена!')
        return
    if vpn.max_conn <= vpn.current_conn:
        await callback.answer('Мест на данный VPN больше нет!')
        return
    if vpn.price == 0:
        if user.trial_until < datetime.now():
            await callback.answer('Пробный период был окончен!')
            return
        vpn_data = await create_access_key(vpn.server_ip, vpn.server_hash)
        scheduler.add_job(
            send_message,
            trigger='date',
            run_date=user.trial_until,
            args=[user.tg_id, vpn_data['id'], vpn.server_ip, vpn.server_hash, vpn.id, vpn.name],
            id= f"{user.tg_id}{vpn_data['id']}"
        )
        await db.add_user_free_vpn(user, vpn_id, 30)
        await callback.message.answer(f'✅<b>Благодарим за использование нашего сервиса!</b>\n\n'
                                      f'Серевер успешно создан!\n<b>Ключ подключения:</b> \n\n'
                                      f'<code>{{vpn_data[\'accessUrl\']}}</code>')
        await callback.answer('Успех!')
    else:
        await state.set_state(st.BuyStars.wait)
        await state.updaet_data(vpn=vpn)
        await callback.message.answer(f'<b>{vpn.name}</b> \n Цена: {vpn.price} RUB в месяц. \n\n')


@client.callback_query(F.data == 'stars')
async def topup_stars(callback: CallbackQuery, state:FSMContext):
    await callback.answer('Произведите оплату')
    data = await state.get_data()
    await callback.message.asnwer_invoice(tittle='Покупка ключа',
    description=f'Покупка ключа {data["vpn"].name} на 30 дней.',
    payload = 'balance',
    currency= 'XTR',
    prices = [LabeledPrice(label='XTR', amount=int(data['vpn'].price / 1))]
    )

@client.pre_checkout_query()
async def pre_checkout_query(query:PreCheckoutQuery):
    await query.answer(True)

@client.message(F.successful_paymant)
async def successful_paymant(message:Message, state:FSMContext, bot:Bot, user: User):
    data = await state.get_data()
    vpn = data['vpn']
    is_vpn = await db.get_user_vpn(user, vpn)
    if vpn.max_conn <= vpn.current_conn or is_vpn:
        await message.answer('🔴Произошла непредвиденная ошибка обратитесь к @')
        await bot.refund_star_payment(message.from_user.id, telegram_paymant_charge_id=message.successful_payment.telegram_payment_charge_id)
        return
    if message.successful_payment.total_amount == vpn.price:
        vpn_data = await create_access_key(vpn.server_ip, vpn.server_hash)
        run_time = datetime.now() + timedelta(days=30)
        scheduler.add_job(
            send_message,
            trigger='date',
            run_date=run_time,
            args=[user.telegram_id, vpn_data['id'], vpn.server_ip, vpn.server_hash, vpn.id, vpn.name],
            id=f"send_msg_{user.tg_id}_{vpn_data['id']}"
        )
        await db.add_user_vpn(user, vpn.id, 30)
        await message.answer(f'✅<b>Благодарим за использование нашего сервиса</b>')

    else:
        await message.answer('Произошла ошибка')
            