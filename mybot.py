from aiogram import types

import sqlite3

from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

from interface.signup import teacher_password_waiting, sign_up_student
from interface.mailing_and_students_feedback import Mailing
from configs.bot_configs import bot, dp, main_menu_message
from interface.teacher_lecture_analytics import get_analytics

conn = sqlite3.connect(r'interface/database/students_feedback.db')
cursor = conn.cursor()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute(f"SELECT user_id, first_name, last_name FROM teachers WHERE user_id = {message.from_user.id}")
    result_t = cursor.fetchone()

    if not result_t:
        cursor.execute(f"SELECT user_id, first_name, last_name FROM students WHERE user_id = {message.from_user.id}")
        result_s = cursor.fetchone()

    if result_t or result_s:
        if result_t:
            await main_menu_message(message,
                                    f"👋Здравствуйте, {result_t[1]} {result_t[2]}", 1)
        else:
            await main_menu_message(message,
                                    f"👋Здравствуйте, {result_s[1]} {result_s[2]}", 0)
    else:
        await message.answer("👋Здравствуйте\n\n"
                             "❌<b>Вы ещё не зарегистрированы.</b>\n"
                             "Для продолжения работы пройдите регистрацию")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["👨‍🏫Я преподаватель", "👨‍🎓Я студент"]
        keyboard.add(*buttons)
        await message.answer("❔Вы <b>преподаватель</b> или <b>студент</b>?", reply_markup=keyboard)


@dp.message_handler(text=['👨‍🏫Я преподаватель', '👨‍🎓Я студент'])
async def sign_up(message: types.Message, state: FSMContext):
    if message.text == '👨‍🏫Я преподаватель':
        await teacher_password_waiting(message, state)
    else:
        await sign_up_student(message, state)


@dp.message_handler(text=['📬Сделать рассылку'])
async def mailing(message: types.Message, state: FSMContext):
    cursor.execute(f"SELECT user_id FROM teachers WHERE user_id = {message.from_user.id}")
    result_t = cursor.fetchone()
    if result_t:
        back_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_menu.add("🏠Вернуться в главное меню")
        await message.answer("🖊Напишите название лекции", reply_markup=back_menu)
        await state.set_state(Mailing.lecture_name)
    else:
        await main_menu_message(message, "⛔️<b>Вы не являетесь преподавателем.</b>", 0)


@dp.message_handler(text=['📊Получить аналитику'])
async def get_report(message: types.Message):
    await get_analytics(message)
