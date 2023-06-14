from aiogram import types
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
menu_btn = ['⟡ Add reminder 📝 ⟡','⟡ View reminders 🔎 ⟡', '⟡ Remindify Bot User Guide ⟡']
menu.add(*menu_btn)

persistent_menu = [
    [
        InlineKeyboardButton(text='Select Month', callback_data='select_month'),
        InlineKeyboardButton(text='Select Day', callback_data='select_day'),
        InlineKeyboardButton(text='Select Hour', callback_data='select_hour'),
        InlineKeyboardButton(text='Select Minute', callback_data='select_minute')
    ]
]


guide_text = '''
📚 Remindify Bot User Guide 📚

Thank you for choosing Remindify, your personal reminder assistant. This user guide will help you get started and make the most out of Remindify's features.

1. Adding a Reminder 📝

To add a reminder, simply type or tap on the "Add reminder" button. You will be prompted to enter the text for your reminder. Please provide the necessary information and press "Send" to proceed.

2. Selecting the Month 🗓️

Once you've entered the reminder text, you will be asked to select the month for your reminder. Use the provided menu to choose the desired month. If the current month is available, you can start selecting the day from today onwards.

3. Selecting the Day, Hour, and Minute ⏰

After choosing the month, you will be presented with a menu to select the day, hour, and minute for your reminder. Use the respective menus to set the desired values.

4. Review and Confirmation ✅

Once you've selected the date and time for your reminder, Remindify will display a summary of your reminder. Review the details and confirm by pressing the "Confirm" button.

That's it! You're now ready to use Remindify to manage your reminders. If you have any questions or need further assistance, feel free to reach out. Enjoy using Remindify! 😊
'''
