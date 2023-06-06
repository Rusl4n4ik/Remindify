from aiogram.dispatcher.filters.state import StatesGroup, State


class Remindify(StatesGroup):
    SET_NOTIFICATION_DATETIME = State()
    REMINDER_TEXT = State()
    SET_TIME = State()
    SET_DAY = State()
    SET_MONTH = State()