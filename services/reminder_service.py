from datetime import datetime, timedelta

import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from services.booking_service import active_bookings


async def check_lunch_reminders(bot: Bot):
    tz = pytz.timezone(settings.timezone)
    now = datetime.now(tz).replace(second=0, microsecond=0)
    target = now + timedelta(minutes=settings.reminder_minutes)
    for booking in active_bookings(target.date()):
        if str(booking.get('start_time')) == target.strftime('%H:%M'):
            try:
                await bot.send_message(int(booking['user_id']), f'Нагадування: ваш обід починається о {booking["start_time"]}.')
            except Exception:
                pass


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    scheduler.add_job(check_lunch_reminders, 'interval', minutes=1, args=[bot])
    scheduler.start()
    return scheduler
