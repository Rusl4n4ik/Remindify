from aiogram import types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
menu_btn = ['⟡ Add reminder 📝 ⟡','⟡ View reminders 🔎 ⟡']
menu.add(*menu_btn)

persistent_menu = [
    [
        InlineKeyboardButton(text='Select Month', callback_data='select_month'),
        InlineKeyboardButton(text='Select Day', callback_data='select_day'),
        InlineKeyboardButton(text='Select Hour', callback_data='select_hour'),
        InlineKeyboardButton(text='Select Minute', callback_data='select_minute')
    ]
]
