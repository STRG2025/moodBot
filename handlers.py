from aiogram import types, Dispatcher, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time
import logging
from config import config
from database import db


bot = Bot(token=config.TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)

async def send_mood_keyboard(chat_id: int) -> int:
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="😊 Хорошее", callback_data="mood_1"),
        types.InlineKeyboardButton(text="😐 Нормальное", callback_data="mood_0"),
        types.InlineKeyboardButton(text="😞 Плохое", callback_data="mood_-1")
    )
    message = await bot.send_message(
        chat_id,
        "Как твое настроение сегодня?",
        reply_markup=builder.as_markup()
    )
    return message.message_id

async def send_daily_notification(user_id: int):
    try:
        await send_mood_keyboard(user_id)
        logger.info(f"Отправлено уведомление пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

async def schedule_notifications():
    try:
        users = await db.get_all_users()
        hour, minute = map(int, config.NOTIFICATION_TIME.split(':'))
        
        for user_id in users:
            scheduler.add_job(
                send_daily_notification,
                'cron',
                day_of_week='mon-sun',
                hour=hour,
                minute=minute,
                args=[user_id],
                id=f"mood_notification_{user_id}"
            )
        
        logger.info(f"Запланированы уведомления для {len(users)} пользователей")
    except Exception as e:
        logger.error(f"Ошибка планирования уведомлений: {e}")

@dp.message(Command("start"))
async def start_command(message: types.Message):
    try:
        await db.save_user(message.from_user)
        await db.update_notification_settings(message.from_user.id, True)
        await message.answer(
            "Привет! Я бот для отслеживания настроения.\n\n"
            "Я буду ежедневно спрашивать о твоем настроении в 9-00\n"
        )
        await send_mood_keyboard(message.chat.id)
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")



@dp.callback_query(lambda c: c.data.startswith('mood_'))
async def process_mood(callback: types.CallbackQuery):
    try:
        mood_value = int(callback.data.split('_')[1])
        user_id = callback.from_user.id
        
        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
        
        await db.save_mood(user_id, mood_value)
        stats = await db.get_user_stats(user_id)
        
        response = (
            f"Записал: {'😊 Хорошее' if mood_value == 1 else '😐 Нормальное' if mood_value == 0 else '😞 Плохое'}\n"
            f"Статистика:\n"
            f"Неделя: {stats['weekly_avg']:.2f}\n"
            f"Месяц: {stats['monthly_avg']:.2f}"
        )
        
        await callback.message.answer(response)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка обработки настроения: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже")

async def on_startup():
    await db.connect()
    await schedule_notifications()
    scheduler.start()
    logger.info("Бот, БД и планировщик успешно запущены")

async def on_shutdown():
    scheduler.shutdown()
    await db.close()
    await bot.session.close()
    logger.info("Бот, БД и планировщик остановлены")

