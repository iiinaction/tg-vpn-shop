from outline_api import delete_access_key
from dao.user_dao import UserDAO

from bot import bot

async def send_message(user, key, url, cert, vpn_id, vpn_name):
    await delete_access_key(key)
    await UserDAO.delete_user_vpn(user, vpn_id)
    await bot.send_message(user, f'❤️‍🩹Закончилось действие вашего VPN: {vpn_name}')

async def send_notification(user, vpn_name):
    await bot.send_message(user, f'❤️‍🩹Осталось 3 дня до окончания действия вашего VPN: {vpn_name} !')

    