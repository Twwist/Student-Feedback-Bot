from aiogram import Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from configs.bot_token import token

bot = Bot(token=token, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())


async def main_menu_message(message, message_text: str, recipient: int):
    '''
    Отправляет главное меню
    :param message: сообщение от пользователя
    :param message_text: текст сообщения
    :param recipient: 1 - преподаватель, 0 - студент
    '''
    if recipient == 1:
        main_teachers_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["📬Сделать рассылку", "📊Получить аналитику"]
        main_teachers_menu.add(*buttons)
        await bot.send_message(message.from_user.id, message_text, reply_markup=main_teachers_menu)
    elif recipient == 0:
        main_students_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Студент button1", "Студент button2"]
        main_students_menu.add(*buttons)
        await bot.send_message(message.from_user.id, message_text, reply_markup=main_students_menu)
