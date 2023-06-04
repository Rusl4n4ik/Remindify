import pytz
from timezonefinder import TimezoneFinder
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime
from aiogram.dispatcher import FSMContext
from keyboard import menu
import asyncio, geopy
from geopy.geocoders import Nominatim
from pytz import timezone
from aiogram.dispatcher.filters import Text

import db
from fms import Reminder

API_TOKEN = '6197051771:AAE3dlqsUL2mp5RZ-9nzsT5qqTga1Jqqx5U'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
tmp = {}


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Here we go!", reply_markup=menu)
    exist_user = db.check_existing(message.chat.id)
    if not exist_user:
        db.add_user(message.chat.id, message.from_user.first_name, message.from_user.username)


@dp.message_handler(text="⟡Add reminder⟡")
async def add_reminder(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id

        await message.reply('Enter your reminder text:')
        await Reminder.REMINDER_TEXT.set()

        await state.update_data(user_id=user_id)  # Store user_id in the state data

    except Exception as e:
        await message.reply('Error adding the reminder.')


@dp.message_handler(state=Reminder.REMINDER_TEXT)
async def enter_reminder_text(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()  # Retrieve the stored state data
        user_id = data.get('user_id')  # Retrieve the user_id from the state data
        reminder_text = message.text

        await message.reply('Please enter the notification date and time in the format DD.MM.YYYY HH:MM (24-hour format):')
        await Reminder.SET_NOTIFICATION_DATETIME.set()

        await state.update_data(reminder_text=reminder_text)  # Store reminder_text in the state data

    except Exception as e:
        await message.reply('Error adding the reminder.')


@dp.message_handler(state=Reminder.SET_NOTIFICATION_DATETIME)
async def set_notification_datetime(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()  # Retrieve the stored state data
        user_id = data.get('user_id')  # Retrieve the user_id from the state data
        reminder_text = data.get('reminder_text')  # Retrieve the reminder_text from the state data

        datetime_format = '%d.%m.%Y %H:%M'
        notification_datetime = datetime.strptime(message.text, datetime_format)

        reminder = db.Reminder(user_id=user_id, text=reminder_text, date=notification_datetime)  # Update the column name to `date`
        db.session.add(reminder)
        db.session.commit()

        time_difference = (notification_datetime - datetime.now()).total_seconds()
        await schedule_reminder_job(user_id, reminder_text, time_difference)

        await bot.send_message(user_id, f'Reminder added: {reminder_text}')

        await state.finish()  # Finish the state after successfully adding the reminder

    except ValueError:
        await message.reply('Invalid date and time format. Please enter the date and time in the format DD.MM.YYYY HH:MM (24-hour format).')


async def schedule_reminder_job(user_id: int, reminder_text: str, time_difference: int):
    async def send_reminder():
        await bot.send_message(user_id, f'Reminder: {reminder_text}')

    # Schedule the reminder job with the specified time difference
    loop = asyncio.get_running_loop()
    loop.call_later(time_difference, asyncio.create_task, send_reminder())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)