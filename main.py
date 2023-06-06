import sqlite3
import pytz
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.engine import cursor
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
conn = sqlite3.connect('remindify.sqlite')
cursor = conn.cursor()


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

        await state.update_data(user_id=user_id)

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


async def schedule_reminder_job(user_id: int, reminder_text: str, time_difference: int):
    async def send_reminder():
        await bot.send_message(user_id, f'Reminder: {reminder_text}')

    # Schedule the reminder job with the specified time difference
    loop = asyncio.get_running_loop()
    loop.call_later(time_difference, asyncio.create_task, send_reminder())


@dp.message_handler(text="⟡View reminders⟡")
async def view_reminders(message: types.Message):
    user_id = message.from_user.id
    reminders = db.get_user_reminders(user_id)

    if not reminders:
        await message.reply('You have no reminders.')
    else:
        keyboard = types.InlineKeyboardMarkup()
        for reminder in reminders:
            button_text = f'{reminder.text} ({reminder.date.strftime("%d.%m.%Y %H:%M")})'
            button = InlineKeyboardButton(text=button_text, callback_data=f'reminder:{reminder.id}')
            keyboard.add(button)

        await message.reply('Here are your reminders:', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('reminder:'))
async def handle_reminder_callback(callback_query: types.CallbackQuery):
    reminder_id = int(callback_query.data.split(':')[1])

    reminder = db.get_reminder_by_id(reminder_id)

    if reminder:
        reminder_text = reminder.text
        reminder_date = reminder.date.strftime('%d.%m.%Y %H:%M')
        await callback_query.answer(f'Reminder: {reminder_text}\nDate: {reminder_date}')
    else:
        await callback_query.answer('Reminder not found.')

    await callback_query.message.delete()


# @dp.callback_query_handler(lambda c: c.data.startswith('reminder:'))
# async def handle_reminder_callback(callback_query: types.CallbackQuery):
#     reminder_id = int(callback_query.data.split(':')[1])
#
#     # Получаем информацию о выбранной заметке из базы данных
#     reminder = db.get_reminder_by_id(reminder_id)
#
#     if reminder:
#         reminder_text = reminder.text
#         reminder_date = reminder.date.strftime('%d.%m.%Y %H:%M')
#
#         keyboard = InlineKeyboardMarkup(row_width=2)
#         edit_button = InlineKeyboardButton(text='Edit', callback_data=f'edit:{reminder_id}')
#         delete_button = InlineKeyboardButton(text='Delete', callback_data=f'delete:{reminder_id}')
#         keyboard.add(edit_button, delete_button)
#
#         await callback_query.answer(f'Reminder: {reminder_text}\nDate: {reminder_date}', show_alert=True)
#         await callback_query.message.edit_reply_markup(reply_markup=keyboard)
#     else:
#         await callback_query.answer('Reminder not found.')
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('edit:'))
# async def handle_edit_callback(callback_query: types.CallbackQuery):
#     reminder_id = int(callback_query.data.split(':')[1])
#
#     reminder = db.get_reminder_by_id(reminder_id)
#
#     if reminder:
#         await Reminder.UPDATE_TEXT.set()
#         await Reminder.UPDATE_ID.set()
#
#         await callback_query.message.answer('Enter the new reminder text:')
#     else:
#         await callback_query.answer('Reminder not found.')
#
#
# @dp.message_handler(state=Reminder.UPDATE_TEXT)
# async def update_text(message: types.Message, state: FSMContext):
#     try:
#         reminder_id = (await state.get_data()).get('reminder_id')
#         new_text = message.text
#
#         db.update_reminder_text(reminder_id, new_text)
#
#         await message.answer('Reminder text updated successfully.')
#         await state.finish()
#
#     except Exception as e:
#         await message.answer('Error updating reminder text.')
#
#
# @dp.callback_query_handler(lambda c: c.data.startswith('delete:'))
# async def handle_delete_callback(callback_query: types.CallbackQuery):
#     reminder_id = int(callback_query.data.split(':')[1])
#
#     await Reminder.DELETE_CONFIRMATION.set()
#     await callback_query.answer('Are you sure you want to delete this reminder?')
#
#
# @dp.callback_query_handler(state=Reminder.DELETE_CONFIRMATION)
# async def delete_reminder_callback(callback_query: types.CallbackQuery, state: FSMContext):
#     if callback_query.data.lower() == 'yes':
#         reminder_id = (await state.get_data()).get('reminder_id')
#
#         db.delete_reminder(reminder_id)
#
#         await callback_query.answer('Reminder deleted successfully.')
#         await callback_query.message.delete()
#
#     else:
#         await callback_query.answer('Reminder deletion cancelled.')
#
#     await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)