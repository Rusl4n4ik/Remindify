from aiogram import types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
menu_btn = ['⟡Add reminder⟡','⟡View reminders⟡']
menu.add(*menu_btn)
