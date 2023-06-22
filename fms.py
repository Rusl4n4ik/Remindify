from aiogram.dispatcher.filters.state import StatesGroup, State


class Remindify(StatesGroup):
    CURRENT_TIME = State()
    REMINDER_TEXT = State()
    SET_DAY = State()
    SET_HOUR = State()
    SET_MINUTE = State()


class UTC(StatesGroup):
    start = State()
    waiting_for_time_zone = State()