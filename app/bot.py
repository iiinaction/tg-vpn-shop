from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import settings
from apscheduler.jobstores.redis import RedisJobStore
from aiogram.fsm.storage.redis import RedisStorage, Redis
from outline_vpn.outline_vpn import OutlineVPN
from apscheduler.schedulers.asyncio import AsyncIOScheduler

#REDIS STORAGE
jobstores = {'default':RedisJobStore(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=settings.REDIS_DB_SCHEDDULER
    )}

redis_fsm = Redis(
    host = settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=settings.REDIS_DB_FSM
    )
storage2 = RedisStorage(redis_fsm)
storage = MemoryStorage()
#Инициализация бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)
admins = settings.ADMIN_IDS

#Работа с API Outline
client = OutlineVPN(api_url=settings.API_URL, cert_sha256=settings.CERT_SHA)

#Работа с задачами sheduler ? 
scheduler = AsyncIOScheduler(gconfig=jobstores)



