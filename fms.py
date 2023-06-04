from aiogram.dispatcher.filters.state import StatesGroup, State


class Reminder(StatesGroup):
    SET_NOTIFICATION_DATETIME = State()
    REMINDER_TEXT = State()