import asyncio
import calendar
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import state
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import session, Session


import db
from fms import Remindify
from keyboard import menu

API_TOKEN = '6197051771:AAE3dlqsUL2mp5RZ-9nzsT5qqTga1Jqqx5U'

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
tmp = {}
conn = sqlite3.connect('remindify.sqlite')
cursor = conn.cursor()


class Reminder:
    def __init__(self, user_id, text, date):
        self.user_id = user_id
        self.text = text
        self.date = date


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Here we go!", reply_markup=menu)
    exist_user = db.check_existing(message.chat.id)
    if not exist_user:
        db.add_user(message.chat.id, message.from_user.first_name, message.from_user.username)


@dp.message_handler(text="⟡Add reminder⟡")
async def add_reminder_command(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id

        await message.reply('Enter your reminder text:')
        await Remindify.REMINDER_TEXT.set()

        await state.update_data(user_id=user_id)

    except Exception as e:
        await message.reply('Error adding the reminder.')


@dp.message_handler(state=Remindify.REMINDER_TEXT)
async def enter_reminder_text(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()  # Retrieve the stored state data
        user_id = data.get('user_id')  # Retrieve the user_id from the state data
        reminder_text = message.text

        await message.reply('Please select the month:', reply_markup=get_month_menu())

        await state.update_data(reminder_text=reminder_text)  # Store reminder_text in the state data

    except Exception as e:
        await message.reply('Error adding the reminder.')


def get_month_menu():
    keyboard = InlineKeyboardMarkup(row_width=4)

    # Add the month buttons to the menu
    for month in range(1, 13):
        button = InlineKeyboardButton(text=calendar.month_name[month], callback_data=f'month:{month}')
        keyboard.insert(button)

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('month:'), state=Remindify.REMINDER_TEXT)
async def set_month(callback_query: types.CallbackQuery, state: FSMContext):
    month = int(callback_query.data.split(':')[1])

    # Store the selected month in the state
    await state.update_data(month=month)
    await Remindify.SET_DAY.set()  # Transition to the SET_DAY state

    await bot.answer_callback_query(callback_query.id, f'Selected month: {calendar.month_name[month]}')

    # Get the selected month and display the day menu
    await bot.send_message(callback_query.from_user.id, 'Please select the day:', reply_markup=get_day_menu())


def get_day_menu():
    keyboard = InlineKeyboardMarkup(row_width=7)

    # Add the day buttons to the menu
    for day in range(1, 32):
        button = InlineKeyboardButton(text=str(day), callback_data=f'day:{day}')
        keyboard.insert(button)

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('day:'), state=Remindify.SET_DAY)
async def set_day(callback_query: types.CallbackQuery, state: FSMContext):
    day = int(callback_query.data.split(':')[1])

    # Store the selected day in the state
    await state.update_data(day=day)
    await Remindify.SET_TIME.set()  # Transition to the SET_TIME state

    await bot.answer_callback_query(callback_query.id, f'Selected day: {day}')

    # Get the selected day and display the time input prompt
    await bot.send_message(callback_query.from_user.id, 'Please enter the reminder time in the format HH:MM (24-hour format):')


@dp.message_handler(state=Remindify.SET_TIME)
async def set_time(message: types.Message, state: FSMContext):
    # Retrieve the stored data from the state
    data = await state.get_data()
    month = data.get('month')
    day = data.get('day')

    try:
        # Parse the user input for time
        time_parts = message.text.strip().split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])

        # Validate the time values
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError('Invalid time format.')

        # Store the selected time in the state
        await state.update_data(hour=hour, minute=minute)
        await Remindify.SET_MONTH.set()  # Transition back to the SET_MONTH state to start a new reminder

        # Retrieve all the stored data
        data = await state.get_data()
        reminder_text = data.get('reminder_text')
        selected_month = data.get('month')
        selected_day = data.get('day')
        selected_hour = data.get('hour')
        selected_minute = data.get('minute')

        # Create a datetime object for the reminder date
        now = datetime.now()
        reminder_date = datetime(now.year, selected_month, selected_day, selected_hour, selected_minute)

        # Create a Reminder instance with the date set
        reminder = Reminder(user_id=data['user_id'], text=reminder_text, date=reminder_date)

        # Save the reminder to the SQLite database
        cursor.execute("INSERT INTO reminders (user_id, text, date) VALUES (?, ?, ?)",
                       (reminder.user_id, reminder.text, reminder.date))
        conn.commit()

        await message.reply('Reminder created successfully!')
        await state.finish()  # Finish the state and reset the data

    except ValueError:
        await message.reply('Invalid time format. Please enter the time in the format HH:MM (24-hour format).')


@dp.message_handler(text="⟡View reminders⟡")
async def view_reminders_command(message: types.Message):
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


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)