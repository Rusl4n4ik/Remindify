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
    current_month = datetime.now().month  # Get the current month
    keyboard = InlineKeyboardMarkup(row_width=4)

    # Add the month buttons to the menu up to December
    for month in range(current_month, current_month + 12):
        month_number = (month - 1) % 12 + 1  # Wrap around to handle months > 12
        if month_number <= 12:
            button = InlineKeyboardButton(text=calendar.month_name[month_number], callback_data=f'month:{month_number}')
            keyboard.insert(button)

    return keyboard


def get_day_menu():
    keyboard = InlineKeyboardMarkup(row_width=7)

    # Add the day buttons to the menu
    for day in range(1, 32):
        button = InlineKeyboardButton(text=str(day), callback_data=f'day:{day}')
        keyboard.insert(button)

    return keyboard


def get_hour_menu():
    keyboard = InlineKeyboardMarkup(row_width=6)

    # Add the hour buttons to the menu
    for hour in range(0, 24):
        button = InlineKeyboardButton(text=str(hour), callback_data=f'hour:{hour}')
        keyboard.insert(button)

    return keyboard


def get_minute_menu():
    keyboard = InlineKeyboardMarkup(row_width=6)

    # Add the minute buttons to the menu
    for minute in range(0, 61, 5):
        button = InlineKeyboardButton(text=str(minute), callback_data=f'minute:{minute}')
        keyboard.insert(button)

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('month:'), state=Remindify.REMINDER_TEXT)
async def set_month(callback_query: types.CallbackQuery, state: FSMContext):
    month = int(callback_query.data.split(':')[1])

    await state.update_data(month=month)
    await Remindify.SET_DAY.set()

    await bot.answer_callback_query(callback_query.id, f'Selected month: {calendar.month_name[month]}')

    # Get the selected month and display the day menu
    await bot.send_message(callback_query.from_user.id, 'Please select the day:', reply_markup=get_day_menu())

    # Update the original message to remove the month menu
    await callback_query.message.edit_reply_markup()
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('day:'), state=Remindify.SET_DAY)
async def set_day(callback_query: types.CallbackQuery, state: FSMContext):
    day = int(callback_query.data.split(':')[1])

    await state.update_data(day=day)
    await Remindify.SET_HOUR.set()

    await bot.answer_callback_query(callback_query.id, f'Selected day: {day}')

    # Get the selected day and display the hour menu
    await bot.send_message(callback_query.from_user.id, 'Please select the hour:', reply_markup=get_hour_menu())

    # Update the original message to remove the day menu
    await callback_query.message.edit_reply_markup()
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('hour:'), state=Remindify.SET_HOUR)
async def set_hour(callback_query: types.CallbackQuery, state: FSMContext):
    hour = int(callback_query.data.split(':')[1])

    await state.update_data(hour=hour)
    await Remindify.SET_MINUTE.set()

    await bot.answer_callback_query(callback_query.id, f'Selected hour: {hour}')

    # Get the selected hour and display the minute menu
    await bot.send_message(callback_query.from_user.id, 'Please select the minute:', reply_markup=get_minute_menu())

    # Update the original message to remove the hour menu
    await callback_query.message.edit_reply_markup()
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data.startswith('minute:'), state=Remindify.SET_MINUTE)
async def set_minute(callback_query: types.CallbackQuery, state: FSMContext):
    minute = int(callback_query.data.split(':')[1])

    await state.update_data(minute=minute)

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
    reminder = db.Reminder(user_id=data['user_id'], text=reminder_text, date=reminder_date)

    # Save the reminder to the database
    db.session.add(reminder)
    db.session.commit()

    # Calculate the time difference between the reminder date and current time
    time_difference = (reminder_date - datetime.now()).total_seconds()

    # Schedule the reminder job
    await schedule_reminder_job(data['user_id'], reminder_text, time_difference)

    await bot.send_message(callback_query.from_user.id, 'Reminder created successfully!')
    await state.finish()  # Finish the state and reset the data
    await callback_query.message.delete()


async def schedule_reminder_job(user_id: int, reminder_text: str, time_difference: int):
    async def send_reminder():
        await bot.send_message(user_id, f'Reminder: {reminder_text}')

    # Schedule the reminder job with the specified time difference
    loop = asyncio.get_running_loop()
    loop.call_later(time_difference, asyncio.ensure_future, send_reminder())


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

        db.delete_reminder(reminder_id)  # Удаление напоминания из базы данных

        # Отправка уведомления о удалении напоминания
        await callback_query.answer(f'Reminder deleted:\n{reminder_text}\nDate: {reminder_date}')

        # Обновление меню со списком напоминаний
        user_id = callback_query.from_user.id
        reminders = db.get_user_reminders(user_id)

        if not reminders:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text='You have no reminders.',
                reply_markup=None  # Убрать клавиатуру из сообщения
            )
        else:
            keyboard = types.InlineKeyboardMarkup()
            for reminder in reminders:
                button_text = f'{reminder.text} ({reminder.date.strftime("%d.%m.%Y %H:%M")})'
                button = InlineKeyboardButton(text=button_text, callback_data=f'reminder:{reminder.id}')
                keyboard.add(button)

            await bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text='Here are your reminders:',
                reply_markup=keyboard
            )
    else:
        await callback_query.answer('Reminder not found.')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)