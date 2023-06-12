from aiogram.dispatcher.filters.state import StatesGroup, State


class Remindify(StatesGroup):
    SET_NOTIFICATION_DATETIME = State()
    REMINDER_TEXT = State()
    SET_DAY = State()
    SET_MONTH = State()
    SET_HOUR = State()
    SET_MINUTE = State()
    SET_TIME = State()
