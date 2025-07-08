from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter, CommandStart, Command
from aiogram.types import Message, CallbackQuery
from app.config import admins
import app.client.keyboards as kb
import app.dao.user_dao as db
import app.states as st
import asyncio

admin = Router()

class AdminProtect(Filter):
    def __init__(self, admins:list[int]):
        self.admins = admins
    
    async def __call__(self, message:Message) -> bool:
        return message.from_user.id in self.admins
    
@admin.message(AdminProtect(), Command("sendall"))
async def sendall_choose_client(message:Message, state:FSMContext):
    await state.clear()
    await state.set_state(st.SendAll.clients)
    await message.answer('Каким пользователям сделать рассылку?', reply_markup= await kb.sendall_choose_client())

@admin.callback_query(AdminProtect(), F.data.startswith('sendall_'), st.SendAll.clients)
async def sendall_message(callback:CallbackQuery, state:FSMContext):
    await callback.answer('')
    clients = callback.data.split('_')[1]
    await state.update_data(clients=clients)
    await state.set_state(st.SendAll.text_message)
    await callback.message.answer('Введите сообщение для рассылки')

@admin.message(AdminProtect(), st.SendAll.text_message)
async def sendall_to_users(message:Message, state:FSMContext):
    tdata = await state.get_data()
    if tdata['clients'] =='all':
        clients = await db.get_all_users()
        for client in clients:
            await asyncio.sleep(1)
            try: 
                await message.send_copy(chat_id=client.telegram_id)
            except:
                continue
    else:
        clients = await  db.get_sendall_users(tdata['clients'])
        print('!!!!!!!!!!!!!!!', client)
        for client in clients:
            print('!!!!!!!!!!!!!', client)
            await asyncio.sleep(1)
            try:
                await message.send_copy(chat_id=client)
            except:
                continue
    await state:clear()
    await message.asnwer('Сообщение отправлено всем пользователям')

    